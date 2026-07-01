from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from signal_engine.retrieval.case_bundle import (
    CASE_BUNDLE_INDEX_STATUS_LABEL,
    CASE_BUNDLE_STATUS_LABEL,
    build_all_case_review_bundles,
    build_case_review_bundle,
    validate_case_review_bundle_file,
)
from signal_engine.retrieval.reviewed_query_set import read_jsonl
from tools.build_case_review_bundle import main as case_bundle_cli


OBJECTS_PATH = Path("data/retrieval/retrieval_object_metadata.jsonl")
FIRST20_QUERY_SET_PATH = Path("data/retrieval/retrieval_reviewed_query_set.first20.jsonl")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def test_single_case_bundle_builds_metadata_only_report(tmp_path: Path) -> None:
    out_path = tmp_path / "HD_2025_Q4.case_review_bundle.json"
    report_path = tmp_path / "HD_2025_Q4.case_review_bundle.md"

    bundle = build_case_review_bundle(
        case_id="HD_2025_Q4",
        objects_path=OBJECTS_PATH,
        query_set_path=FIRST20_QUERY_SET_PATH,
        out_path=out_path,
        report_path=report_path,
    )

    assert bundle["status_label"] == CASE_BUNDLE_STATUS_LABEL
    assert bundle["case_id"] == "hd_2025_q4"
    assert bundle["ticker"] == "HD"
    assert bundle["fiscal_period"] == "2025 Q4"
    assert bundle["object_count"] == 22
    assert bundle["reviewed_query_count"] == 1
    assert bundle["reviewed_eligible_query_count"] == 0
    assert bundle["readiness_flags"]["has_retrieval_objects"] is True
    assert bundle["readiness_flags"]["has_reviewed_query_rows"] is True
    assert bundle["readiness_flags"]["has_reviewed_eligible_query_rows"] is False
    assert bundle["readiness_flags"]["llm_review_ready"] is False
    assert bundle["readiness_flags"]["benchmark_ready"] is False
    assert bundle["no_raw_text"] is True
    assert bundle["provider_execution"] is False
    assert bundle["embeddings_generated"] is False
    assert bundle["vector_db_generated"] is False
    assert bundle["evaluated_retrieval_quality"] is False
    assert bundle["production_claims"] is False
    assert "reviewed_queries_pending" in bundle["blocked_reasons"]
    assert "llm_review_disabled" in bundle["blocked_reasons"]
    assert out_path.exists()
    assert report_path.exists()
    encoded = json.dumps(bundle, sort_keys=True).lower()
    assert '"raw_text"' not in encoded
    assert '"chunk_text"' not in encoded
    assert '"provider_response"' not in encoded


def test_all_case_index_builds_one_bundle_per_available_case(tmp_path: Path) -> None:
    index = build_all_case_review_bundles(
        objects_path=OBJECTS_PATH,
        query_set_path=FIRST20_QUERY_SET_PATH,
        out_dir=tmp_path,
    )

    assert index["status_label"] == CASE_BUNDLE_INDEX_STATUS_LABEL
    assert index["case_count"] == 31
    assert index["bundle_count"] == 31
    assert index["provider_execution"] is False
    assert index["embeddings_generated"] is False
    assert index["vector_db_generated"] is False
    assert index["evaluated_retrieval_quality"] is False
    assert index["production_claims"] is False
    assert (tmp_path / "case_review_bundle_index.json").exists()
    assert (tmp_path / "case_review_bundle_index.md").exists()
    assert len(list(tmp_path.glob("*.case_review_bundle.json"))) == 31
    hd_summary = next(case for case in index["cases"] if case["case_id"] == "hd_2025_q4")
    assert hd_summary["object_count"] == 22
    assert hd_summary["reviewed_query_count"] == 1
    assert hd_summary["reviewed_eligible_query_count"] == 0
    assert hd_summary["readiness_status"] == "case_review_pending_only"


def test_unknown_case_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown case_id"):
        build_case_review_bundle(
            case_id="missing_2099_q9",
            objects_path=OBJECTS_PATH,
            query_set_path=FIRST20_QUERY_SET_PATH,
            out_path=tmp_path / "missing.case_review_bundle.json",
            report_path=tmp_path / "missing.case_review_bundle.md",
        )


def test_bundle_validation_accepts_valid_bundle_and_index(tmp_path: Path) -> None:
    bundle_path = tmp_path / "HD_2025_Q4.case_review_bundle.json"
    build_case_review_bundle(
        case_id="HD_2025_Q4",
        objects_path=OBJECTS_PATH,
        query_set_path=FIRST20_QUERY_SET_PATH,
        out_path=bundle_path,
        report_path=tmp_path / "HD_2025_Q4.case_review_bundle.md",
    )
    build_all_case_review_bundles(
        objects_path=OBJECTS_PATH,
        query_set_path=FIRST20_QUERY_SET_PATH,
        out_dir=tmp_path / "all",
    )

    bundle_summary = validate_case_review_bundle_file(bundle_path)
    index_summary = validate_case_review_bundle_file(tmp_path / "all" / "case_review_bundle_index.json")

    assert bundle_summary["status_label"] == CASE_BUNDLE_STATUS_LABEL
    assert bundle_summary["case_id"] == "hd_2025_q4"
    assert index_summary["status_label"] == CASE_BUNDLE_INDEX_STATUS_LABEL
    assert index_summary["case_count"] == 31


def test_bundle_validation_rejects_raw_text_fields_missing_provenance_and_overclaims(tmp_path: Path) -> None:
    bundle_path = tmp_path / "HD_2025_Q4.case_review_bundle.json"
    build_case_review_bundle(
        case_id="HD_2025_Q4",
        objects_path=OBJECTS_PATH,
        query_set_path=FIRST20_QUERY_SET_PATH,
        out_path=bundle_path,
        report_path=tmp_path / "HD_2025_Q4.case_review_bundle.md",
    )

    raw_payload = _load_json(bundle_path)
    raw_payload["retrieval_object_refs"][0]["raw_text"] = "blocked"
    raw_path = tmp_path / "raw.case_review_bundle.json"
    raw_path.write_text(json.dumps(raw_payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden"):
        validate_case_review_bundle_file(raw_path)

    missing_provenance = _load_json(bundle_path)
    missing_provenance["provenance_refs"] = []
    missing_path = tmp_path / "missing.case_review_bundle.json"
    missing_path.write_text(json.dumps(missing_provenance, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="provenance_refs must not be empty"):
        validate_case_review_bundle_file(missing_path)

    overclaim = _load_json(bundle_path)
    overclaim["evaluated_retrieval_quality"] = True
    overclaim["readiness_flags"]["benchmark_ready"] = True
    overclaim_path = tmp_path / "overclaim.case_review_bundle.json"
    overclaim_path.write_text(json.dumps(overclaim, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="evaluated_retrieval_quality must be false"):
        validate_case_review_bundle_file(overclaim_path)


def test_cross_case_query_object_refs_are_rejected(tmp_path: Path) -> None:
    query_rows = read_jsonl(FIRST20_QUERY_SET_PATH)
    object_rows = read_jsonl(OBJECTS_PATH)
    bac_object = next(row for row in object_rows if row["case_id"] == "bac_2025_q4")
    query_rows[0]["case_id"] = "hd_2025_q4"
    query_rows[0]["expected_object_ids"] = [bac_object["object_id"]]
    query_rows[0]["evidence_object_id_refs"] = [bac_object["object_id"]]
    query_rows[0]["provenance_refs"] = [bac_object["provenance_ref"]]
    corrupt_query_set = tmp_path / "cross_case.jsonl"
    _write_jsonl(corrupt_query_set, query_rows)

    with pytest.raises(ValueError, match="does not match case_id"):
        build_case_review_bundle(
            case_id="HD_2025_Q4",
            objects_path=OBJECTS_PATH,
            query_set_path=corrupt_query_set,
            out_path=tmp_path / "HD_2025_Q4.case_review_bundle.json",
            report_path=tmp_path / "HD_2025_Q4.case_review_bundle.md",
        )


def test_case_bundle_cli_modes_build_and_validate_without_provider_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "bundles"
    assert (
        case_bundle_cli(
            [
                "--all-cases",
                "--objects",
                str(OBJECTS_PATH),
                "--query-set",
                str(FIRST20_QUERY_SET_PATH),
                "--out-dir",
                str(out_dir),
            ]
        )
        == 0
    )
    assert case_bundle_cli(["--validate", str(out_dir / "case_review_bundle_index.json")]) == 0

    generated_names = {path.name.lower() for path in out_dir.iterdir()}
    assert not any("embedding" in name for name in generated_names)
    assert not any("vector" in name for name in generated_names)
    assert not any("provider_artifact" in name for name in generated_names)
    index = _load_json(out_dir / "case_review_bundle_index.json")
    assert index["provider_execution"] is False
    assert index["embeddings_generated"] is False
    assert index["vector_db_generated"] is False
    assert index["evaluated_retrieval_quality"] is False
