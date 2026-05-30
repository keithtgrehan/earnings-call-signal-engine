from __future__ import annotations

import json
from pathlib import Path

from tools.build_first100_calibration_batch import build_calibration_batch


def _candidate(label: str, index: int) -> dict[str, str]:
    return {
        "candidate_id": f"cand{index}",
        "case_id": f"case{index}",
        "ticker": "HD",
        "fiscal_period": "2025 Q4",
        "suggested_label": label,
        "suggested_confidence": "0.55",
        "evidence_object_id": f"evidence{index}",
        "chunk_id": f"chunk{index}",
        "retrieval_object_id": f"object{index}",
        "source_path": "/Users/keith/Desktop/earnings calls 100 samples/HD/chunk.txt",
        "source_sha256": "sha256:" + "a" * 64,
        "normalized_transcript_hash": "sha256:" + "b" * 64,
        "text_hash": "sha256:" + "c" * 64,
        "provenance_hash": "sha256:" + "d" * 64,
        "speaker_role": "management",
        "transcript_section": "prepared_remarks",
        "rule_id": "rule",
        "rule_version": "first100_deterministic_v1",
        "contamination_flags": "machine_candidate_only;not_gold",
        "gold_status": "not_gold",
        "review_status": "pending_human_review",
        "raw_text_committed": "false",
    }


def test_calibration_batch_keeps_rows_not_gold(tmp_path: Path, monkeypatch) -> None:
    labels = [
        "guidance_statement",
        "analyst_pressure",
        "management_hedging",
        "uncertainty",
        "neutral/no_signal",
    ]
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text("".join(json.dumps(_candidate(labels[i % len(labels)], i)) + "\n" for i in range(20)), encoding="utf-8")
    monkeypatch.setattr("tools.build_first100_calibration_batch.SUMMARY_REPORT", tmp_path / "summary.md")

    summary = build_calibration_batch(candidates, tmp_path / "calibration.jsonl")
    rows = [json.loads(line) for line in (tmp_path / "calibration.jsonl").read_text(encoding="utf-8").splitlines()]

    assert summary["calibration_rows"] == len(rows)
    assert rows
    assert all(row["gold_status"] == "not_gold" for row in rows)
    assert all(row["final_label"] == "" for row in rows)
    assert "raw phrase" not in str(rows).lower()
