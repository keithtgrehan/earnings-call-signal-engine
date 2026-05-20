from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "src", ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_duckdb_analytics import analytics_payload, write_report as write_duckdb_report  # noqa: E402
from export_argilla_dataset import export_reviews  # noqa: E402
from import_argilla_reviews import import_reviews  # noqa: E402
from run_review_evaluation import evaluate  # noqa: E402
from signal_engine.review_schema import CANONICAL_REVIEW_FIELDS  # noqa: E402
from signal_engine.storage.sqlite_store import init_db, table_names  # noqa: E402


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
                "transcript_path": "data/corpus/NVDA/transcript.txt",
            }
        ]
    )

    assert len(exported) == 1
    row = exported[0]
    assert row["metadata"]["provenance_id"] == "cand-1"
    assert row["fields"]["evidence_text"] == "We expect continued demand growth."
    assert set(CANONICAL_REVIEW_FIELDS) <= set(row["metadata"])


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
    exported[0]["responses"] = [{"question_name": "reviewer_action", "value": "accept"}]
    exported[0]["reviewer_id"] = "reviewer_a"

    reviews, gold = import_reviews(exported)

    assert len(reviews) == 1
    assert len(gold) == 1
    assert gold[0]["review_id"] == reviews[0]["review_id"]
    assert gold[0]["provenance_id"] == "cand-2"
    assert gold[0]["label_source"] == "argilla_human_review"


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


def test_sqlite_schema_initializes_required_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "signal_engine.db"
    connection = init_db(db_path)

    assert {
        "corpus_cases",
        "review_records",
        "gold_labels",
        "provenance_events",
        "evaluation_runs",
    } <= table_names(connection)
    connection.close()
    with sqlite3.connect(db_path) as raw_connection:
        count = raw_connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'").fetchone()[0]
    assert count >= 5


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
