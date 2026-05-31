from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.build_first100_reviewer_packet import build_reviewer_packet


def _write_candidate(path: Path, candidate_id: str, suggested_label: str = "guidance_statement") -> None:
    row = {
        "candidate_id": candidate_id,
        "case_id": "fake_2025_q4",
        "ticker": "FAKE",
        "fiscal_period": "2025 Q4",
        "suggested_label": suggested_label,
        "gold_status": "not_gold",
        "review_status": "pending_human_review",
        "raw_text_committed": "false",
        "training_allowed": "false",
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def test_reviewer_packet_is_reports_only_and_does_not_modify_staging_draft(tmp_path: Path) -> None:
    root = tmp_path
    candidates = root / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
    candidates.parent.mkdir(parents=True)
    _write_candidate(candidates, "sha256:1111111111111111111111111")
    _write_candidate(candidates, "sha256:2222222222222222222222222", suggested_label="analyst_pressure")
    draft = root / "data" / "review" / "staging" / "first100_adjudication_draft.jsonl"
    draft.write_text("\n", encoding="utf-8")
    before = draft.read_bytes()

    md_out = root / "reports" / "review" / "first100_reviewer_packet.md"
    json_out = root / "reports" / "review" / "first100_reviewer_packet.json"
    summary = build_reviewer_packet(
        root=root,
        candidates_path=candidates,
        draft_path=draft,
        md_out=md_out,
        json_out=json_out,
    )

    assert draft.read_bytes() == before
    assert summary["status"] == "REVIEW_PACKET_READY"
    assert summary["candidate_count"] == 2
    assert summary["candidate_ids"] == ["sha256:1111111111111111111111111", "sha256:2222222222222222222222222"]
    assert summary["staging_draft_modified"] is False
    assert summary["gold_labels_created"] == 0
    assert summary["promotion_ready"] is False
    assert summary["training_ready"] is False
    assert summary["training_data_created"] is False
    assert str(md_out.relative_to(root)).startswith("reports/review/")
    assert str(json_out.relative_to(root)).startswith("reports/review/")

    packet_text = md_out.read_text(encoding="utf-8")
    packet_json = json.loads(json_out.read_text(encoding="utf-8"))
    assert "docs/review/first100_manual_adjudication_guide.md" in packet_text
    assert "docs/review/first100_adjudication_row_template.json" in packet_text
    assert "python3 tools/validate_first100_adjudication_file.py data/review/staging/first100_adjudication_draft.jsonl" in packet_text
    assert "sha256:1111111111111111111111111" in packet_text
    assert "reviewer" in packet_text
    assert "adjudicated_label" in packet_text
    assert "suggested_label" not in packet_text
    assert "guidance_statement" not in packet_text
    assert "analyst_pressure" not in packet_text
    assert packet_json["candidate_ids"] == summary["candidate_ids"]
    assert packet_json["promotion_ready"] is False
    assert packet_json["training_ready"] is False


def test_reviewer_packet_missing_candidate_metadata_fails_closed(tmp_path: Path) -> None:
    root = tmp_path
    draft = root / "data" / "review" / "staging" / "first100_adjudication_draft.jsonl"
    draft.parent.mkdir(parents=True)
    draft.write_text("\n", encoding="utf-8")

    summary = build_reviewer_packet(
        root=root,
        candidates_path=root / "data" / "review" / "staging" / "missing.jsonl",
        draft_path=draft,
        md_out=root / "reports" / "review" / "first100_reviewer_packet.md",
        json_out=root / "reports" / "review" / "first100_reviewer_packet.json",
    )

    assert summary["status"] == "NOT_READY"
    assert summary["candidate_count"] == 0
    assert summary["candidate_ids"] == []
    assert summary["promotion_ready"] is False
    assert summary["training_ready"] is False
    assert "candidate metadata missing" in summary["blockers"]


def test_reviewer_packet_rejects_outputs_outside_reports_review(tmp_path: Path) -> None:
    root = tmp_path
    candidates = root / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
    candidates.parent.mkdir(parents=True)
    _write_candidate(candidates, "sha256:1111111111111111111111111")
    draft = root / "data" / "review" / "staging" / "first100_adjudication_draft.jsonl"
    draft.write_text("\n", encoding="utf-8")

    with pytest.raises(ValueError, match="reports/review"):
        build_reviewer_packet(
            root=root,
            candidates_path=candidates,
            draft_path=draft,
            md_out=root / "data" / "review" / "bad_packet.md",
            json_out=root / "reports" / "review" / "first100_reviewer_packet.json",
        )
