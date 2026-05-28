from __future__ import annotations

import json
from pathlib import Path

from signal_engine.transcripts.normalize import normalize_transcript_metadata, run_dry_run


ROOT = Path(__file__).resolve().parents[1]


def test_normalized_transcript_schema_requires_contract_fields() -> None:
    schema = json.loads((ROOT / "schemas" / "normalized_transcript.schema.json").read_text(encoding="utf-8"))

    assert {
        "case_id",
        "ticker",
        "source_asset_id",
        "source_sha256",
        "source_type",
        "rights_status",
        "sections",
        "speaker_turns",
        "qa_pairs",
        "prepared_remarks",
        "provenance",
        "raw_text_committed",
    }.issubset(set(schema["required"]))


def test_normalizer_serializes_hashes_and_spans_not_raw_text() -> None:
    raw_phrase = "SYNTHETIC RAW NORMALIZATION PHRASE"
    payload = normalize_transcript_metadata(
        case_id="jpm_2025_q1",
        ticker="JPM",
        source_asset_id="asset_fixture",
        source_type="company_ir",
        rights_status="approved_manual_local",
        text=f"Prepared remarks\n{raw_phrase}\nQuestion-and-Answer\nAnalyst: Question?\nManagement: Answer.",
        provenance={"source_ref": "fixture"},
    )
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["raw_text_committed"] is False
    assert payload["source_sha256"].startswith("sha256:")
    assert payload["text_sha256"].startswith("sha256:")
    assert payload["sections"]
    assert payload["speaker_turns"]
    assert payload["qa_pairs"]
    assert raw_phrase not in serialized


def test_dry_run_report_proves_no_raw_text_serialization(tmp_path: Path) -> None:
    report = tmp_path / "normalization_readiness.md"
    raw_phrase = "SYNTHETIC DRY RUN RAW PHRASE"

    summary = run_dry_run(report_path=report, synthetic_text=f"Prepared remarks\n{raw_phrase}\nQuestion-and-Answer\nAnalyst: Q?\nManagement: A.")

    assert summary["raw_text_committed"] is False
    assert summary["raw_phrase_serialized"] is False
    assert raw_phrase not in report.read_text(encoding="utf-8")
