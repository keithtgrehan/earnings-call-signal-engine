from __future__ import annotations

import json
from pathlib import Path

from tools.build_first30_review_packets import build_packets


def test_review_packets_exclude_raw_evidence_text(tmp_path: Path, monkeypatch) -> None:
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(
        json.dumps(
            {
                "candidate_id": "cand1",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "fiscal_period": "2025 Q4",
                "label": "guidance_statement",
                "retrieval_object_id": "obj1",
                "span_start_char": "1",
                "span_end_char": "9",
                "provenance_hash": "sha256:" + "a" * 64,
                "gold_status": "not_gold",
                "review_status": "pending_human_review",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.build_first30_review_packets.SUMMARY_REPORT", tmp_path / "summary.md")

    summary = build_packets(candidates, tmp_path / "packets")

    packet_text = (tmp_path / "packets" / "first30_batch_001_guidance.md").read_text(encoding="utf-8")
    assert summary["candidate_count"] == 1
    assert "Raw evidence text included: false" in packet_text
    assert "guidance outlook raw phrase" not in packet_text
