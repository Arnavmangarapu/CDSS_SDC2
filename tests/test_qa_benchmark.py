import pytest
import json

from evaluation.run_qa_benchmark import question_payload, summarize
from evaluation.run_qa_benchmark import digest
from evaluation.summarize_qa_benchmark import export


def example(i, gold="A"):
    return {"case_id": str(i), "dataset": "MedQA", "question": "Question?",
            "context": "", "options": dict(zip("ABCDE", "abcde")),
            "gold": gold, "explanation": "SECRET REFERENCE"}


def test_reference_fields_never_enter_answer_prompt():
    assert set(question_payload(example(0))) == {"question", "context", "options"}
    assert "SECRET REFERENCE" not in str(question_payload(example(0)))


def test_five_choice_micro_specificity_matches_one_vs_rest_counts():
    cases = [example(i) for i in range(50)]
    records = [{"case_id": str(i), "mode": "llm_only", "status": "ok",
                "answer": "A" if i < 47 else "B"} for i in range(50)]
    metrics = summarize(cases, records)["MedQA"]["llm_only"]
    assert metrics["accuracy"] == .94
    assert metrics["precision_micro"] == metrics["recall_micro"] == metrics["f1_micro"] == .94
    assert metrics["specificity_micro_one_vs_rest"] == .985
    assert metrics["complete"]


def test_failures_are_counted_and_partial_runs_are_marked():
    cases = [example(i) for i in range(3)]
    records = [{"case_id": "0", "mode": "llm_only", "status": "ok", "answer": "A"},
               {"case_id": "1", "mode": "llm_only", "status": "error"}]
    metrics = summarize(cases, records)["MedQA"]["llm_only"]
    assert metrics["accuracy"] == .5
    assert metrics["failures"] == 1
    assert not metrics["complete"]
    assert metrics["precision_micro"] is None
    assert metrics["specificity_micro_one_vs_rest"] is None


def test_three_class_specificity_is_not_binary_accuracy():
    cases = [dict(example(i), dataset="PubMedQA", options={s: s for s in ("yes", "no", "maybe")}, gold="yes") for i in range(2)]
    records = [{"case_id": str(i), "mode": "llm_only", "status": "ok", "answer": a}
               for i, a in enumerate(("yes", "no"))]
    assert summarize(cases, records)["PubMedQA"]["llm_only"]["specificity_micro_one_vs_rest"] == .75


def test_paper_export_refuses_incomplete_matrix(tmp_path):
    (tmp_path / "cases.json").write_text(json.dumps([example(0)]))
    (tmp_path / "manifest.json").write_text(json.dumps({"cases_sha256": digest(tmp_path / "cases.json")}))
    (tmp_path / "records.jsonl").write_text("")
    with pytest.raises(ValueError, match="Incomplete"):
        export(tmp_path, tmp_path / "paper")
    assert not (tmp_path / "paper.md").exists()


def test_explicit_partial_export_does_not_invent_missing_pairs(tmp_path):
    cases = [example(0), example(1)]
    records = [{"case_id": "0", "mode": "llm_only", "status": "ok", "answer": "A"}]
    (tmp_path / "cases.json").write_text(json.dumps(cases))
    (tmp_path / "manifest.json").write_text(json.dumps({"cases_sha256": digest(tmp_path / "cases.json")}))
    (tmp_path / "records.jsonl").write_text(json.dumps(records[0])+"\n")
    (tmp_path / "metrics.json").write_text(json.dumps(summarize(cases, records)))
    export(tmp_path, tmp_path / "partial", allow_partial=True)
    result = json.loads((tmp_path / "partial.json").read_text())
    assert not result["complete"]
    assert result["recorded_attempts"] == 1
    assert result["planned_attempts"] == 4
    assert result["paired_discordances"]["MedQA"]["paired_cases"] == 0
    assert "INCOMPLETE" in (tmp_path / "partial.md").read_text()
