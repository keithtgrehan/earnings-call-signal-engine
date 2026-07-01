from __future__ import annotations

import json
from pathlib import Path

from tools import report_first100_training_readiness as readiness


def _candidate(index: int) -> dict[str, str]:
    return {
        "candidate_id": f"cand{index}",
        "source_sha256": "sha256:" + "a" * 64,
        "normalized_transcript_hash": "sha256:" + "b" * 64,
        "provenance_hash": "sha256:" + "c" * 64,
    }


def test_first100_training_readiness_review_ready_not_training_ready(tmp_path: Path, monkeypatch) -> None:
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text("".join(json.dumps(_candidate(i)) + "\n" for i in range(100)), encoding="utf-8")
    packets = tmp_path / "packets"
    packets.mkdir()
    for index in range(5):
        (packets / f"first100_batch_00{index + 1}.md").write_text("# packet\n", encoding="utf-8")
    monkeypatch.setattr(readiness, "PACKET_DIR", packets)
    monkeypatch.setattr(readiness, "_training_rights_explicit", lambda: False)

    summary = readiness.report(candidates, tmp_path / "missing-promotion.json", tmp_path / "report.md", tmp_path / "report.json")

    assert summary["state"] == "REVIEW_READY"
    assert summary["training_performed"] is False
    assert summary["valid_adjudicated_labels"] == 0
    assert "explicit training rights are not configured" in summary["blockers"]
