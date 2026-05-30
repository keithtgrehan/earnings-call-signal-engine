from __future__ import annotations

import json
from pathlib import Path

from tools.build_first100_review_packets import build_packets


def test_first100_review_packets_exclude_raw_evidence_text(tmp_path: Path, monkeypatch) -> None:
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(
        json.dumps(
            {
                "candidate_id": "cand1",
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "fiscal_period": "2025 Q4",
                "suggested_label": "guidance_statement",
                "suggested_confidence": "0.70",
                "retrieval_object_id": "obj1",
                "evidence_object_id": "evidence1",
                "chunk_id": "chunk1",
                "source_path": "/Users/keith/Desktop/earnings calls 100 samples/JPM/chunk.txt",
                "source_sha256": "sha256:" + "a" * 64,
                "normalized_transcript_hash": "sha256:" + "b" * 64,
                "text_hash": "sha256:" + "c" * 64,
                "provenance_hash": "sha256:" + "d" * 64,
                "speaker_role": "management",
                "transcript_section": "prepared_remarks",
                "rule_id": "guidance_statement_terms",
                "rule_version": "first100_deterministic_v1",
                "contamination_flags": "machine_candidate_only;not_gold",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.build_first100_review_packets.SUMMARY_REPORT", tmp_path / "summary.md")

    summary = build_packets(candidates, tmp_path / "packets")

    packet_text = (tmp_path / "packets" / "first100_batch_001_guidance.md").read_text(encoding="utf-8")
    assert summary["candidate_count"] == 1
    assert "MACHINE CANDIDATE ONLY: guidance_statement" in packet_text
    assert "Raw evidence text included: false" in packet_text
    assert "guidance outlook raw phrase" not in packet_text
