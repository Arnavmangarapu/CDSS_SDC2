"""Prepare a source/aggregate review bundle without publishing or source books."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
SAFE_JSON = {'evaluation/med_safety_cases.v1.json', 'evaluation/medqa_selection.v1.json',
             'evaluation/protocol.draft.example.json', 'evaluation/safety_live_pilot.protocol.json'}
PAPER_AGGREGATES = {'PAIRED_DEVELOPMENT_RESULTS_20261031.json', 'SAFETY_BASELINE_REGRESSION_20261031.json',
                    'BASE_PAPER_COMPARISON_20261031.json', 'SAFETY_LIVE_DEVELOPMENT_RESULTS_20261031.json',
                    'CORPUS_AUDIT_20261031.json', 'EVALUATION_ENVIRONMENT_20261031.json',
                    'SAFETY_LIVE_PROTOCOL_CHAIN_20261031.json'}


def allowed(path):
    p = Path(path)
    if p.suffix == '.py' and p.parts[0] in {'backend', 'evaluation', 'ingestion', 'tests'}: return True
    if path in SAFE_JSON or path in {'requirements.txt', '.env.example', 'paper/release/README.md'}: return True
    if p.parts[0] == 'evaluation' and p.suffix == '.md': return True
    return p.parts[0] == 'paper' and p.name in PAPER_AGGREGATES


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): p.error('Preserve previous bundles; choose a new path')
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    paths = sorted(s for s in tracked if s and allowed(s))
    # Aggregates may be newly prepared and not committed until the final documentation checkpoint.
    for n in PAPER_AGGREGATES:
        path = 'paper/'+n
        if (ROOT/path).is_file() and path not in paths: paths.append(path)
    manifest = {'status':'local_review_candidate_not_public_release',
                'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'files':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sorted(paths)},
                'excluded':'Books, publisher source snapshots, raw examination questions/answers, model outputs, databases, credentials, .git history and author-contact manuscript files',
                'reproduction_limits':'Protected source snapshots and ontology/model inputs must be acquired separately under applicable terms. This bundle does not certify rights clearance or independent clinical validation.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(args.output,'x',compression=ZIP_DEFLATED) as z:
        for s in sorted(paths): z.write(ROOT/s,s)
        z.writestr('REVIEW_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'files':len(paths),
                      'archive_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__': main()
