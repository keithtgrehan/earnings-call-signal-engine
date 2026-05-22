from __future__ import annotations

import json
from pathlib import Path

from signal_engine.gold_review import audit_gold_labels, build_first_100_queue, validate_promotion_rows


def test_gold_audit_does_not_modify_canonical_file(tmp_path: Path) -> None:
    gold = tmp_path / "gold_labels.jsonl"
    row = {
        "case_id": "case_1",
        "label_id": "label_1",
        "signal_type": "guidance_revision",
        "direction": "positive",
        "speaker_role": "management",
        "evidence_text": "We raised revenue guidance.",
        "reviewer": "human",
        "reviewed_at": "2026-01-01",
        "source_file": "manual-local://case_1",
        "provenance_hash": "sha256:abc",
    }
    gold.write_text(json.dumps(row) + "\n", encoding="utf-8")
    before = gold.read_text(encoding="utf-8")
    summary = audit_gold_labels(gold)
    assert summary["valid_count"] == 1
    assert gold.read_text(encoding="utf-8") == before


def test_gold_audit_blocks_external_duplicate_empty_evidence(tmp_path: Path) -> None:
    gold = tmp_path / "gold_labels.jsonl"
    rows = [
        {
            "case_id": "case_1",
            "label_id": "dup",
            "signal_type": "guidance_revision",
            "direction": "positive",
            "speaker_role": "management",
            "evidence_text": "",
            "reviewer": "human",
            "reviewed_at": "2026-01-01",
            "source_file": "manual-local://case_1",
            "provenance_hash": "sha256:abc",
        },
        {
            "case_id": "case_2",
            "label_id": "dup",
            "signal_type": "uncertainty",
            "direction": "negative",
            "speaker_role": "management",
            "evidence_text": "Demand is uncertain.",
            "reviewer": "human",
            "reviewed_at": "2026-01-01",
            "source_file": "benchmark",
            "source_type": "external_dataset",
            "provenance_hash": "sha256:def",
        },
    ]
    gold.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    statuses = {item["status"] for item in audit_gold_labels(gold)["audited"]}
    assert "BLOCKED_DUPLICATE" in statuses


def test_first_100_parser_marks_candidates_not_gold(tmp_path: Path) -> None:
    packet = tmp_path / "human_labeling_packet.md"
    packet.write_text(
        "## case_1\n### c1\ncandidate_id: c1\ncase_id: case_1\nsuggested_label: uncertainty\nsuggested_confidence: medium\nsource_file: manual://x\nevidence_text: Demand is uncertain.\n",
        encoding="utf-8",
    )
    pool, queue = build_first_100_queue([packet])
    assert len(pool) == 1
    assert queue[0]["gold_status"] == "not_gold"
    assert queue[0]["review_status"] == "pending_human_review"


def test_promotion_validator_rejects_contamination_and_weak_labels() -> None:
    rows = [
        {
            "label_id": "l1",
            "case_id": "c1",
            "final_label": "uncertainty",
            "review_status": "reviewed",
            "gold_status": "promotion_candidate",
            "reviewer": "human",
            "reviewed_at": "2026-01-01",
            "evidence_text": "Demand is uncertain.",
            "source_file": "manual://x",
            "provenance_hash": "sha256:abc",
            "contamination_flags": ["unresolved_source"],
        },
        {
            "label_id": "l2",
            "case_id": "c2",
            "final_label": "uncertainty",
            "review_status": "reviewed",
            "gold_status": "promotion_candidate",
            "reviewer": "human",
            "reviewed_at": "2026-01-01",
            "evidence_text": "Demand is uncertain.",
            "source_file": "manual://y",
            "provenance_hash": "sha256:def",
            "weak_label_only": True,
        },
    ]
    errors = validate_promotion_rows(rows)
    assert any("unresolved contamination" in error for error in errors)
    assert any("weak_label_only" in error for error in errors)


def test_promotion_validator_rejects_external_dataset_rows() -> None:
    errors = validate_promotion_rows(
        [
            {
                "label_id": "l3",
                "case_id": "c3",
                "final_label": "uncertainty",
                "review_status": "reviewed",
                "gold_status": "promotion_candidate",
                "reviewer": "human",
                "reviewed_at": "2026-01-01",
                "evidence_text": "A benchmark answer string.",
                "source_file": "external://financebench",
                "source_type": "external_dataset",
                "provenance_hash": "sha256:ghi",
            }
        ]
    )
    assert any("external_dataset" in error for error in errors)
