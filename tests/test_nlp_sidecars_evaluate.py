from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.nlp_sidecars.evaluate import write_case_evaluation_summary


def test_write_case_evaluation_summary_builds_pairwise_report(tmp_path: Path) -> None:
    base = tmp_path / "outputs" / "demo_case" / "model_sidecars"
    left = base / "finbert_tone"
    right = base / "financial_roberta"
    left.mkdir(parents=True)
    right.mkdir(parents=True)

    run_summary = {
        "case_id": "demo_case",
        "status": "ok",
        "model_kind": "classification",
        "runtime_s": 1.2,
        "units_processed": 2,
        "unit_type_counts": {"chunks": 2},
    }
    for path, model_name, label in (
        (left, "finbert_tone", "positive"),
        (right, "financial_roberta", "negative"),
    ):
        payload = dict(run_summary, model_name=model_name)
        (path / "run_summary.json").write_text(json.dumps(payload), encoding="utf-8")
        (path / "scored_rows.csv").write_text(
            "case_id,unit_type,unit_id,text,top_label,top_score,comparable_label\n"
            f"demo_case,chunks,chunk_0001,Text one,{label},0.9,{label}\n"
            f"demo_case,chunks,chunk_0002,Text two,{label},0.8,{label}\n",
            encoding="utf-8",
        )

    paths = write_case_evaluation_summary(case_id="demo_case", output_root=tmp_path / "outputs")
    summary = json.loads(paths["comparison_summary"].read_text(encoding="utf-8"))

    assert sorted(summary["models_covered"]) == ["financial_roberta", "finbert_tone"]
    assert summary["pairwise_classification"][0]["rows_compared"] == 2
    assert summary["pairwise_classification"][0]["top_label_agreement_rate"] == 0.0


def test_write_case_evaluation_summary_handles_missing_case_dir(tmp_path: Path) -> None:
    paths = write_case_evaluation_summary(case_id="missing_case", output_root=tmp_path / "outputs")
    summary = json.loads(paths["comparison_summary"].read_text(encoding="utf-8"))
    markdown = paths["comparison_markdown"].read_text(encoding="utf-8")

    assert summary["models_covered"] == []
    assert summary["pairwise_classification"] == []
    assert "No prior sidecar outputs were found for this case yet." in summary["notes"]
    assert "No saved sidecar model outputs were present yet." in markdown
