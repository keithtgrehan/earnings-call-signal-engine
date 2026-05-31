from __future__ import annotations

import json
from pathlib import Path

from tools import build_review_readiness_dashboard as dashboard


def _write_csv(path: Path, header: str = "id\n", row: str = "one\n") -> None:
    path.write_text(header + row, encoding="utf-8")


def test_review_dashboard_makes_training_and_promotion_blockers_explicit(tmp_path: Path, monkeypatch) -> None:
    for name in ("transcripts.csv", "normalized.csv", "chunks.csv", "evidence.csv", "retrieval.csv"):
        _write_csv(tmp_path / name)
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(json.dumps({"candidate_id": "fake", "suggested_label": "neutral/no_signal", "case_id": "fake_case"}) + "\n", encoding="utf-8")
    calibration = tmp_path / "calibration.jsonl"
    calibration.write_text(json.dumps({"candidate_id": "fake"}) + "\n", encoding="utf-8")
    promotion = tmp_path / "promotion.json"
    promotion.write_text(json.dumps({"status": "NOT_READY", "valid": False, "rows": 0}), encoding="utf-8")
    adjudication = tmp_path / "adjudication.json"
    adjudication.write_text(
        json.dumps({"status": "NOT_READY", "manifest_exists": True, "adjudicated_rows": 0, "valid": False}),
        encoding="utf-8",
    )
    training = tmp_path / "training.json"
    training.write_text(
        json.dumps(
            {
                "state": "REVIEW_READY",
                "valid_adjudicated_labels": 0,
                "training_rights_explicit": False,
                "training_ready": False,
            }
        ),
        encoding="utf-8",
    )
    packets = tmp_path / "packets"
    packets.mkdir()
    (packets / "first100_batch_001_guidance.md").write_text("# packet\n", encoding="utf-8")
    monkeypatch.setattr(dashboard, "TRANSCRIPT_REGISTRY", tmp_path / "transcripts.csv")
    monkeypatch.setattr(dashboard, "NORMALIZED", tmp_path / "normalized.csv")
    monkeypatch.setattr(dashboard, "CHUNKS", tmp_path / "chunks.csv")
    monkeypatch.setattr(dashboard, "EVIDENCE", tmp_path / "evidence.csv")
    monkeypatch.setattr(dashboard, "RETRIEVAL", tmp_path / "retrieval.csv")
    monkeypatch.setattr(dashboard, "CANDIDATES", candidates)
    monkeypatch.setattr(dashboard, "CALIBRATION", calibration)
    monkeypatch.setattr(dashboard, "PROMOTION", promotion)
    monkeypatch.setattr(dashboard, "ADJUDICATION_VALIDATION", adjudication)
    monkeypatch.setattr(dashboard, "TRAINING", training)
    monkeypatch.setattr(dashboard, "PACKET_DIR", packets)

    summary = dashboard.build_dashboard(tmp_path / "dashboard.md", tmp_path / "dashboard.json")

    assert summary["adjudication_draft_exists"] is True
    assert summary["adjudication_draft_status"] == "NOT_READY"
    assert summary["adjudication_draft_rows"] == 0
    assert summary["adjudicated_rows"] == 0
    assert summary["promotion_manifest_status"] == "NOT_READY"
    assert summary["training_ready"] is False
    assert summary["explicit_training_rights"] is False
    text = (tmp_path / "dashboard.md").read_text(encoding="utf-8")
    assert "Adjudication draft status: NOT_READY" in text
    assert "Empty adjudication scaffold initialized: true" in text
    assert "Promotion manifest status: NOT_READY" in text
    assert "Explicit training rights: false" in text
