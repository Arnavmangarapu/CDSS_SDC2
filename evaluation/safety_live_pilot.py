"""Two-call development safety comparison using the unchanged production extractor.

Private JSONL retains raw LLM JSON and merged context. Public summary contains
counts/IDs only. No source/model changes or new independent labels are made.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path

from backend.agents.clarifier import ClinicalClarifier
from backend.services.entity_linker import EntityLinker
from backend.services.ontology_parser import OntologyParser
from backend.services.llm_fallback import LLMFallback
from backend.services.telemetry import capture_timings, totals
from evaluation.controlled import controlled_transport, configure_llm, require_model, DailyQuotaReached
from evaluation.freeze import ROOT, validate_protocol
from evaluation.paired_statistics import exact_mcnemar, holm
from evaluation.run_med_safety import evaluate_case, sha256
from evaluation.safety_v2 import run_case, score
from ingestion.authoritative_sources import DEFAULT_MANIFEST, build_passages, load_manifest

MODES = ('deterministic', 'llm_only', 'hybrid_fixed_proposal', 'llm_rule_filtered')


class ExtractionTap:
    """Pass-through observer; preserves prompt, validation and provider behavior."""
    def __init__(self, original):
        self.original = original
        self.parsed = None

    def __getattr__(self, name):
        return getattr(self.original, name)

    def generate_json(self, *args, **kwargs):
        self.parsed = deepcopy(self.original.generate_json(*args, **kwargs))
        return deepcopy(self.parsed)


def observe_extraction(clarifier, text):
    original = clarifier.llm
    tap = ExtractionTap(original)
    clarifier.llm = tap
    try:
        context = clarifier.process(text)
        require_model(original)
        if tap.parsed is None:
            raise RuntimeError('Production extraction did not return valid model JSON')
        return context, tap.parsed, original.response_trace()
    finally:
        clarifier.llm = original


def names(items, key):
    return sorted({str(i.get(key, '')).strip().casefold() for i in items if isinstance(i, dict) and i.get(key)})


def extraction_checks(case, raw, context):
    expected = case['structured_facts']
    intended = sorted({i['name'].strip().casefold() for i in expected['medication_statements'] if i['status'] == 'current'})
    raw_current = names([i for i in raw.get('medication_statements', []) if isinstance(i, dict) and i.get('status') == 'current'], 'name')
    statements = lambda items: sorted({(i['name'].strip().casefold(), i['status']) for i in items})
    raw_statements = sorted({(str(i.get('name', '')).strip().casefold(), i.get('status'))
                             for i in raw.get('medication_statements', []) if isinstance(i, dict)})
    quotes = [i.get('source_phrase') for field in ('medication_statements', 'allergy_statements')
              for i in raw.get(field, []) if isinstance(i, dict)]
    merged = context.model_dump()
    return {
        'raw_current_medications_match': raw_current == intended,
        'raw_medication_name_status_match': raw_statements == statements(expected['medication_statements']),
        'raw_allergy_substance_match': names(raw.get('allergy_statements', []), 'substance') == names(expected['allergies'], 'text'),
        'raw_emitted_source_phrases': len(quotes),
        'raw_exact_source_phrases': sum(isinstance(q, str) and bool(q) and q in case['case_text'] for q in quotes),
        'merged_allergy_status_match': context.allergy_status == expected['allergy_status'],
        'merged_medication_list_status_match': context.medication_list_status == expected['medication_list_status'],
        'merged_current_medications_match': names([i for i in merged['medication_statements'] if i['status'] == 'current'], 'name') == intended,
    }


def rule_filter(llm_row, hybrid_row):
    """Filter the SAME emitted warnings, without adding missed warnings.

    The deterministic rule result uses the separately observed production context
    and supplied trusted label passages. This is a post-processing ablation with
    an extra extraction call, not a general semantic verifier or equal-cost arm.
    """
    row = {'case_id': llm_row['case_id'], 'mode': 'llm_rule_filtered'}
    if llm_row.get('status') != 'ok' or hybrid_row.get('status') != 'ok':
        return {**row, 'status': 'error', 'error_type': 'DependencyFailed'}
    actual = set(llm_row['actual_warning_types']) & set(hybrid_row['actual_warning_types'])
    supported = set(llm_row['actual_supported_warning_types']) & set(hybrid_row['actual_supported_warning_types']) & actual
    return {**row, 'status': 'ok', 'actual_warning_types': sorted(actual),
            'actual_supported_warning_types': sorted(supported), 'derived_from_same_llm_generation': True}


def summarize(cases, records, extraction):
    result = score(cases, records, MODES)
    by_key = {(r['case_id'], r['mode']): r for r in records}
    correct = {m: [] for m in MODES}
    for case in cases:
        for m in MODES:
            r = by_key[(case['case_id'], m)]
            correct[m].append(r.get('status') == 'ok' and set(r['actual_warning_types']) == set(case['expected_warning_types'])
                              and set(r['actual_supported_warning_types']) == set(case['expected_supported_warning_types']))
    pairs = []
    for a, b in combinations(MODES, 2):
        a_only = sum(x and not y for x, y in zip(correct[a], correct[b]))
        b_only = sum(y and not x for x, y in zip(correct[a], correct[b]))
        pairs.append({'a': a, 'b': b, 'a_only_exact': a_only, 'b_only_exact': b_only,
                      'exact_mcnemar_p': exact_mcnemar(a_only, b_only)})
    for r, p in zip(pairs, holm([r['exact_mcnemar_p'] for r in pairs])):
        r['holm_adjusted_p'] = p
    result['paired_exact_case_decisions_exploratory'] = pairs
    checks = ('raw_current_medications_match', 'raw_medication_name_status_match', 'raw_allergy_substance_match',
              'merged_allergy_status_match', 'merged_medication_list_status_match', 'merged_current_medications_match')
    result['extraction'] = {k: {'correct': sum(r.get('checks', {}).get(k) is True for r in extraction),
                               'planned': len(cases)} for k in checks}
    result['extraction']['completed'] = sum(r.get('status') == 'ok' for r in extraction)
    result['extraction']['raw_allergy_status'] = 'Not requested by the unchanged production JSON schema; no raw status accuracy is inferred'
    result['extraction']['raw_medication_list_status'] = 'Not requested by the unchanged production JSON schema'
    result['extraction']['source_phrase_grounding'] = {
        'exact': sum(r.get('checks', {}).get('raw_exact_source_phrases', 0) for r in extraction),
        'emitted': sum(r.get('checks', {}).get('raw_emitted_source_phrases', 0) for r in extraction)}
    result['case_scores'] = [{'case_id': c['case_id'], **{m: correct[m][i] for m in MODES}} for i, c in enumerate(cases)]
    traces = [r.get('provider_trace', {}) for r in records if r['mode'] in ('llm_only', 'hybrid_fixed_proposal')]
    result['returned_model_versions'] = sorted({t['returned_model_version'] for t in traces if t.get('returned_model_version')})
    result['missing_model_version_traces'] = sum(not t.get('returned_model_version') for t in traces)
    result.update(evidence_role='development', label_status='Reused developer-authored cases; no independent clinical review',
                  interpretation='Fixed proposal and supplied label passages. Not full-report generation, live retrieval or clinical prescribing validation. Rule-filter arm reuses LLM warning generation and requires an additional production extraction call. Raw extraction name comparisons are exact and developer-labeled; empty target sets can be easy controls.')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases', type=Path, required=True); p.add_argument('--protocol', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): p.error('Preserve earlier attempts; output exists')
    protocol = validate_protocol(args.protocol, args.cases)
    if protocol['evidence_role'] != 'development' or protocol.get('runner') != 'evaluation.safety_live_pilot':
        p.error('This pilot requires its own frozen development protocol')
    cases = json.loads(args.cases.read_text())['cases']
    if not cases or len({c['case_id'] for c in cases}) != len(cases): p.error('Unique nonempty cases required')
    ontology = [ROOT/'datasets/ontologies/hpo/hp.obo', ROOT/'datasets/ontologies/mondo/mondo.obo', ROOT/'datasets/drugcentral/structures.smiles.tsv']
    if any(not f.is_file() for f in ontology): p.error('Production ontology input missing')
    hashes = {str(f.relative_to(ROOT)): sha256(f) for f in ontology}
    if protocol.get('ontology_sha256') != hashes: p.error('Ontology inputs differ from frozen protocol')
    parser = OntologyParser(*map(str, ontology)); parser.parse_all()
    clarifier = ClinicalClarifier(EntityLinker(parser.lookup_table))
    llm = LLMFallback()
    pinned = [x for entries in build_passages(load_manifest()).values() for x, _ in entries]
    labels = [x for x in pinned if x.source_type == 'drug_label']
    args.output.mkdir(parents=True)
    manifest = {'status': 'started', 'clinical_validation': False, 'evidence_role': 'development',
                'created_utc': datetime.now(timezone.utc).isoformat(), 'protocol_sha256': sha256(args.protocol),
                'protocol': protocol, 'planned_cases': len(cases), 'modes': MODES,
                'inference_budget': 'One warning call and one unchanged production extraction call per case; no regeneration'}
    records, extraction = [], []
    def save(name, row):
        with (args.output/name).open('a', encoding='utf-8') as stream: stream.write(json.dumps(row, default=str)+'\n')
    try:
        with controlled_transport(protocol['model'], interval=4.2, retries=3,
                                  event_sink=lambda e: save('transport.jsonl', e)):
            configure_llm(clarifier.llm); configure_llm(llm)
            for i, case in enumerate(cases):
                rows = {'deterministic': run_case(case, 'deterministic', pinned, labels)}
                order = ('llm_only', 'hybrid_fixed_proposal') if i % 2 == 0 else ('hybrid_fixed_proposal', 'llm_only')
                for mode in order:
                    try:
                        with capture_timings() as events:
                            if mode == 'llm_only': row = run_case(case, mode, pinned, labels, llm=llm)
                            else:
                                context, raw, trace = observe_extraction(clarifier, case['case_text'])
                                row = {**evaluate_case(case, 'production_clarifier', pinned, labels, context),
                                       'case_id': case['case_id'], 'mode': mode, 'status': 'ok', 'provider_trace': trace}
                                er = {'case_id': case['case_id'], 'status': 'ok', 'raw_model_json': raw,
                                      'merged_context': context.model_dump(), 'checks': extraction_checks(case, raw, context)}
                                extraction.append(er); save('extraction.private.jsonl', er)
                        row['timings_ms'] = totals(events)
                    except Exception as exc:
                        row = {'case_id': case['case_id'], 'mode': mode, 'status': 'error', 'error_type': type(exc).__name__}
                        if mode == 'hybrid_fixed_proposal':
                            er = {'case_id': case['case_id'], 'status': 'error', 'error_type': type(exc).__name__}
                            extraction.append(er); save('extraction.private.jsonl', er)
                        save('records.jsonl', row)
                        if isinstance(exc, DailyQuotaReached): raise
                        rows[mode] = row; records.append(row); continue
                    rows[mode] = row; records.append(row); save('records.jsonl', row)
                rows['llm_rule_filtered'] = rule_filter(rows['llm_only'], rows['hybrid_fixed_proposal'])
                for mode in ('deterministic', 'llm_rule_filtered'):
                    records.append(rows[mode]); save('records.jsonl', rows[mode])
                print(json.dumps({'completed_cases': i+1, 'planned': len(cases)}), flush=True)
        validate_protocol(args.protocol, args.cases)
        if any(sha256(ROOT/f) != h for f,h in hashes.items()): raise ValueError('Ontology inputs changed during run')
        result = summarize(cases, records, extraction)
        result.update(cases_sha256=sha256(args.cases), source_manifest_sha256=sha256(DEFAULT_MANIFEST))
        (args.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
        manifest['status'] = 'complete'
    except BaseException as exc:
        manifest.update(status='interrupted', error_type=type(exc).__name__)
        raise
    finally:
        (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__': main()
