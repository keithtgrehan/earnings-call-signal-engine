from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

from tools.build_first100_review_spreadsheet import build_review_spreadsheet
from tools.build_first100_weak_model_assist import build_weak_model_assist


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _registry(path: Path) -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "assets": [
                    {
                        "asset_id": "fixture_unknown_model",
                        "asset_type": "model",
                        "name": "Fixture Unknown Model",
                        "source_url": "https://example.com/model",
                        "local_path": "",
                        "license": "unknown",
                        "license_status": "unknown_fail_closed",
                        "permitted_uses": [],
                        "blocked_reason": "license not verified",
                        "requires_download": False,
                        "download_performed": False,
                        "raw_data_committed": False,
                        "model_weights_committed": False,
                        "notes": "No model may be used in tests.",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_weak_model_assist_is_metadata_only_and_never_final_adjudication(tmp_path: Path) -> None:
    raw_phrase = "RAW PHRASE MUST NOT APPEAR"
    candidates = tmp_path / "candidates.jsonl"
    calibration = tmp_path / "calibration.jsonl"
    registry = _registry(tmp_path / "registry.yml")
    out_csv = tmp_path / "assist.csv"
    out_report = tmp_path / "assist.md"
    _write_jsonl(
        candidates,
        [
            {
                "candidate_id": "cand_disagree",
                "case_id": "case1",
                "ticker": "AAA",
                "fiscal_period": "2025 Q1",
                "suggested_label": "guidance_statement",
                "suggested_confidence": "0.70",
                "rule_id": "guidance_revision_terms",
                "source_sha256": "sha256:" + "a" * 64,
                "normalized_transcript_hash": "sha256:" + "b" * 64,
                "provenance_hash": "sha256:" + "c" * 64,
                "evidence_text": raw_phrase,
            },
            {
                "candidate_id": "cand_neutral",
                "case_id": "case2",
                "ticker": "BBB",
                "fiscal_period": "2025 Q2",
                "suggested_label": "neutral/no_signal",
                "suggested_confidence": "0.20",
                "rule_id": "no_signal_metadata_fallback",
                "source_sha256": "sha256:" + "d" * 64,
                "normalized_transcript_hash": "sha256:" + "e" * 64,
                "provenance_hash": "sha256:" + "f" * 64,
            },
            {
                "candidate_id": "cand_missing_source",
                "case_id": "case3",
                "ticker": "CCC",
                "fiscal_period": "2025 Q3",
                "suggested_label": "uncertainty",
                "suggested_confidence": "0.62",
                "rule_id": "uncertainty_terms",
                "normalized_transcript_hash": "sha256:" + "g" * 64,
                "provenance_hash": "sha256:" + "h" * 64,
            },
        ],
    )
    _write_jsonl(calibration, [{"candidate_id": "cand_disagree"}])

    summary = build_weak_model_assist(
        candidates_path=candidates,
        calibration_path=calibration,
        registry_path=registry,
        out_csv=out_csv,
        out_report=out_report,
    )

    rows = list(csv.DictReader(out_csv.open(encoding="utf-8")))
    assert summary["rows"] == 3
    assert summary["final_adjudication_automated"] is False
    assert "adjudicated_label" not in rows[0]
    assert rows[0]["weak_model_suggested_label"] == "guidance_revision"
    assert rows[0]["disagreement_flag"] == "true"
    assert rows[0]["review_priority"] == "highest"
    assert rows[1]["review_priority"] == "low"
    assert rows[2]["review_priority"] == "needs_source_review"
    assert all(row["assist_method"] == "metadata_rule_heuristic" for row in rows)
    assert all(row["allowed_for_final_adjudication"] == "false" for row in rows)
    assert all(row["gold_created"] == "false" for row in rows)
    assert all(row["training_performed"] == "false" for row in rows)
    assert all(row["raw_text_used"] == "false" for row in rows)
    assert all(row["raw_text_returned"] == "false" for row in rows)
    assert raw_phrase not in out_csv.read_text(encoding="utf-8")
    assert raw_phrase not in out_report.read_text(encoding="utf-8")


def test_review_spreadsheet_combines_weak_assist_without_raw_text(tmp_path: Path) -> None:
    raw_phrase = "RAW SPREADSHEET PHRASE"
    assist_csv = tmp_path / "assist.csv"
    out_csv = tmp_path / "accelerator.csv"
    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(
        candidates,
        [
            {
                "candidate_id": "cand1",
                "case_id": "case1",
                "ticker": "AAA",
                "fiscal_period": "2025 Q1",
                "suggested_label": "guidance_statement",
                "evidence_text": raw_phrase,
            }
        ],
    )
    assist_csv.write_text(
        "candidate_id,case_id,ticker,fiscal_period,existing_suggested_label,weak_model_suggested_label,weak_model_confidence,assist_method,disagreement_flag,review_priority,reason_code,allowed_for_final_adjudication,gold_created,training_performed,raw_text_used,raw_text_returned\n"
        "cand1,case1,AAA,2025 Q1,guidance_statement,guidance_statement,0.55,metadata_rule_heuristic,false,medium,metadata_only,false,false,false,false,false\n",
        encoding="utf-8",
    )

    summary = build_review_spreadsheet(candidates_path=candidates, weak_assist_csv=assist_csv, out_csv=out_csv)

    rows = list(csv.DictReader(out_csv.open(encoding="utf-8")))
    assert summary["rows"] == 1
    assert rows[0]["packet_file"] == "data/review/packets/first100_batch_001_guidance.md"
    assert rows[0]["your_label"] == ""
    assert rows[0]["rationale"] == ""
    assert rows[0]["done"] == ""
    assert "evidence_text" not in rows[0]
    assert raw_phrase not in out_csv.read_text(encoding="utf-8")
