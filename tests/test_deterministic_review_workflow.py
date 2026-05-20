from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "src", ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
if str(ROOT / "scripts" / "review") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "review"))

from bootstrap_argilla import is_local_url  # noqa: E402
from build_duckdb_analytics import analytics_payload, write_report as write_duckdb_report  # noqa: E402
from export_argilla_dataset import export_reviews  # noqa: E402
from import_argilla_reviews import import_reviews  # noqa: E402
from run_review_pipeline_dryrun import run_dryrun  # noqa: E402
from run_review_evaluation import evaluate  # noqa: E402
from signal_engine.review_schema import CANONICAL_REVIEW_FIELDS, build_export_manifest, validate_transition  # noqa: E402
from signal_engine.storage.sqlite_store import init_db, insert_provenance_event, insert_review_record, review_action_counts, table_names  # noqa: E402


def test_argilla_export_preserves_provenance_and_evidence() -> None:
    exported = export_reviews(
        [
            {
                "candidate_id": "cand-1",
                "case_id": "NVDA_2026_Q4",
                "signal_type": "opportunity_commitment",
                "evidence_text": "We expect continued demand growth.",
                "transcript_section": "prepared_remarks",
                "speaker_role": "management",
                "confidence": 0.82,
                "source_url": "https://example.com/nvda",
            }
        ]
    )

    assert len(exported) == 1
    row = exported[0]
    assert row["metadata"]["provenance_id"] == "cand-1"
    assert row["fields"]["evidence_text"] == "We expect continued demand growth."
    assert set(CANONICAL_REVIEW_FIELDS) <= set(row["metadata"])


def test_argilla_bootstrap_local_url_guard() -> None:
    assert is_local_url("http://localhost:6900")
    assert is_local_url("http://127.0.0.1:6900")
    assert not is_local_url("https://argilla.example.com")


def test_argilla_import_accept_creates_gold_label_with_provenance() -> None:
    exported = export_reviews(
        [
            {
                "candidate_id": "cand-2",
                "case_id": "META_2025_Q4",
                "signal_type": "risk_friction",
                "evidence_text": "Costs remain a headwind this quarter.",
                "confidence": 0.71,
            }
        ]
    )
    manifest = build_export_manifest([row["metadata"] for row in exported], source_path="fixture", output_path="export")
    exported[0]["responses"] = [{"question_name": "reviewer_action", "value": "accept"}]
    exported[0]["reviewer_id"] = "reviewer_a"

    reviews, gold = import_reviews(exported, export_manifest=manifest)

    assert len(reviews) == 1
    assert len(gold) == 1
    assert gold[0]["review_id"] == reviews[0]["review_id"]
    assert gold[0]["provenance_id"] == "cand-2"
    assert gold[0]["label_source"] == "argilla_human_review"
    assert reviews[0]["review_status"] == "accepted"


def test_argilla_import_rejects_invalid_review_action() -> None:
    exported = export_reviews(
        [
            {
                "candidate_id": "cand-3",
                "case_id": "NFLX_2025_Q1",
                "signal_type": "uncertainty_hedging",
                "evidence_text": "It is too early to call the full-year impact.",
            }
        ]
    )
    exported[0]["responses"] = [{"question_name": "reviewer_action", "value": "approve"}]
    exported[0]["reviewer_id"] = "reviewer_a"

    try:
        import_reviews(exported)
    except ValueError as exc:
        assert "invalid action" in str(exc)
    else:
        raise AssertionError("invalid Argilla review row should fail closed")


def test_argilla_import_rejects_lineage_mismatch() -> None:
    exported = export_reviews(
        [
            {
                "candidate_id": "cand-4",
                "case_id": "NVDA_2026_Q4",
                "signal_type": "opportunity_commitment",
                "evidence_text": "Demand growth remains visible.",
            }
        ]
    )
    manifest = build_export_manifest([row["metadata"] for row in exported], source_path="fixture", output_path="export")
    exported[0]["metadata"]["provenance_id"] = "changed"
    exported[0]["responses"] = [{"question_name": "reviewer_action", "value": "accept"}]
    exported[0]["reviewer_id"] = "reviewer_a"

    try:
        import_reviews(exported, export_manifest=manifest)
    except ValueError as exc:
        assert "provenance_id" in str(exc)
    else:
        raise AssertionError("changed provenance_id should fail closed")


def test_sqlite_schema_initializes_required_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "signal_engine.db"
    connection = init_db(db_path)

    assert {
        "corpus_cases",
        "review_records",
        "gold_labels",
        "provenance_events",
        "evaluation_runs",
        "schema_version",
    } <= table_names(connection)
    connection.close()
    with sqlite3.connect(db_path) as raw_connection:
        count = raw_connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'").fetchone()[0]
    assert count >= 5


def test_sqlite_persists_review_and_provenance(tmp_path: Path) -> None:
    connection = init_db(tmp_path / "signal_engine.db")
    review = export_reviews(
        [
            {
                "candidate_id": "cand-sql",
                "case_id": "FDX_2025_Q4",
                "signal_type": "risk_friction",
                "evidence_text": "Demand remains soft.",
            }
        ]
    )[0]["metadata"]
    insert_review_record(connection, review)
    insert_provenance_event(
        connection,
        {
            "schema_version": "provenance_event_v1",
            "provenance_id": "cand-sql",
            "review_id": review["review_id"],
            "case_id": "FDX_2025_Q4",
            "event_type": "exported",
            "payload": {"source": "test"},
        },
    )
    connection.commit()
    assert review_action_counts(connection) == {"pending": 1}
    assert connection.execute("SELECT COUNT(*) FROM provenance_events").fetchone()[0] == 1


def test_review_evaluation_counts_mismatches() -> None:
    metrics = evaluate(
        [
            {
                "review_id": "r1",
                "case_id": "SBUX_2025_Q4",
                "signal_type": "risk_friction",
                "predicted_direction": "negative",
                "evidence_text": "Traffic was pressured.",
                "transcript_section": "q_and_a",
            },
            {"review_id": "r2", "case_id": "FDX_2025_Q4", "signal_type": "neutral", "evidence_text": "Operator instructions."},
        ],
        [
            {
                "review_id": "r1",
                "case_id": "SBUX_2025_Q4",
                "signal_type": "risk_friction",
                "direction": "mixed",
                "evidence_text": "Traffic was pressured in the afternoon.",
                "transcript_section": "prepared_remarks",
            }
        ],
    )

    assert metrics["tp"] == 1
    assert metrics["fp"] == 1
    assert metrics["direction_mismatch"] == 1
    assert metrics["evidence_mismatch"] == 1
    assert metrics["section_mismatch"] == 1
    assert metrics["schema_version"] == "review_evaluator_v1"
    assert metrics["evidence_mismatch_classes"]["section_mismatch"] == 1


def test_duckdb_analytics_report_builds_without_duckdb_dependency(tmp_path: Path) -> None:
    payload = analytics_payload(
        [{"reviewer_id": "reviewer_a", "reviewer_action": "uncertain"}],
        [{"transcript_section": "q_and_a"}],
        {"tp": 1, "fp": 2, "fn": 3, "evidence_mismatch": 1},
    )
    report = tmp_path / "duckdb.md"
    write_duckdb_report(report, payload, duckdb_available=False)

    text = report.read_text(encoding="utf-8")
    assert "DuckDB Review Analytics" in text
    assert "uncertainty_rate" in text
    assert payload["reviewer_counts"] == {"reviewer_a": 1}


def test_review_state_transition_validation() -> None:
    assert validate_transition("pending", "in_review")
    assert validate_transition("in_review", "accepted")
    assert not validate_transition("rejected", "accepted")


def test_dryrun_pipeline_is_idempotent(tmp_path: Path) -> None:
    fixture = ROOT / "tests" / "fixtures" / "review_workflow" / "deterministic_outputs.jsonl"
    first = run_dryrun(fixture, tmp_path / "dryrun")
    second = run_dryrun(fixture, tmp_path / "dryrun")

    assert first["exported_rows"] == second["exported_rows"] == 2
    assert first["gold_labels"] == second["gold_labels"] == 1
    assert (tmp_path / "dryrun" / "signal_engine.db").exists()


def test_staged_transcript_guard_pattern() -> None:
    forbidden = ("case/raw/transcript.txt", "case/processed/transcript_clean.txt", "case/labels/human_labeling_packet.md")
    allowed = ("schemas/review/exported_review_row.schema.json", "tests/fixtures/review_workflow/deterministic_outputs.jsonl")
    assert all(("raw/transcript.txt" in path or "processed/" in path or "labels/" in path) for path in forbidden)
    assert not any(("raw/transcript.txt" in path or "processed/" in path or "labels/" in path) for path in allowed)
