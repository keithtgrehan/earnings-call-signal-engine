from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

DB_SCHEMA_VERSION = 2

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS corpus_cases (
    case_id TEXT PRIMARY KEY,
    ticker TEXT,
    company_name TEXT,
    fiscal_year TEXT,
    quarter TEXT,
    transcript_path TEXT,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending_review',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_records (
    review_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    provenance_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    topic TEXT,
    transcript_section TEXT,
    speaker_role TEXT,
    evidence_text TEXT NOT NULL,
    evidence_start_hint TEXT,
    evidence_end_hint TEXT,
    predicted_direction TEXT,
    reviewer_action TEXT,
    reviewer_notes TEXT,
    confidence REAL NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    source_url TEXT,
    transcript_path TEXT,
    created_at TEXT NOT NULL,
    reviewer_id TEXT,
    assigned_reviewer_id TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending',
    reviewer_action_audit TEXT NOT NULL DEFAULT '',
    disagreement_status TEXT NOT NULL DEFAULT 'none',
    adjudication_notes TEXT NOT NULL DEFAULT '',
    evidence_mismatch_class TEXT NOT NULL DEFAULT 'none',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES corpus_cases(case_id)
);

CREATE TABLE IF NOT EXISTS gold_labels (
    id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    review_id TEXT,
    provenance_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    direction TEXT,
    evidence_text TEXT NOT NULL,
    transcript_section TEXT,
    speaker_role TEXT,
    reviewer_id TEXT,
    source_url TEXT,
    transcript_path TEXT,
    evidence_mismatch_class TEXT NOT NULL DEFAULT 'none',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES review_records(review_id),
    FOREIGN KEY (case_id) REFERENCES corpus_cases(case_id)
);

CREATE TABLE IF NOT EXISTS provenance_events (
    event_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    provenance_id TEXT NOT NULL,
    review_id TEXT,
    case_id TEXT,
    event_type TEXT NOT NULL,
    source_path TEXT,
    source_url TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    run_type TEXT NOT NULL,
    deterministic_output_path TEXT,
    gold_label_path TEXT,
    metrics_json TEXT NOT NULL,
    report_path TEXT,
    review_count INTEGER NOT NULL DEFAULT 0,
    accepted_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    uncertain_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_records_case_id ON review_records(case_id);
CREATE INDEX IF NOT EXISTS idx_review_records_provenance_id ON review_records(provenance_id);
CREATE INDEX IF NOT EXISTS idx_review_records_status ON review_records(review_status);
CREATE INDEX IF NOT EXISTS idx_gold_labels_case_id ON gold_labels(case_id);
CREATE INDEX IF NOT EXISTS idx_provenance_events_provenance_id ON provenance_events(provenance_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_runs_created_at ON evaluation_runs(created_at);
"""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_event_id(*parts: Any) -> str:
    payload = "||".join(str(part or "") for part in parts)
    return "event_" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str | Path) -> sqlite3.Connection:
    connection = connect(db_path)
    connection.executescript(SCHEMA_SQL)
    migrate(connection)
    connection.commit()
    return connection


def migrate(connection: sqlite3.Connection) -> None:
    now = utc_now()
    connection.execute(
        """
        INSERT INTO schema_version (id, version, applied_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET version=excluded.version, applied_at=excluded.applied_at
        """,
        (DB_SCHEMA_VERSION, now),
    )


def table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {str(row["name"]) for row in rows}


def upsert_corpus_case(connection: sqlite3.Connection, row: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO corpus_cases (case_id, ticker, company_name, fiscal_year, quarter, transcript_path, source_url, status)
        VALUES (:case_id, :ticker, :company_name, :fiscal_year, :quarter, :transcript_path, :source_url, :status)
        ON CONFLICT(case_id) DO UPDATE SET
            ticker=excluded.ticker,
            company_name=excluded.company_name,
            fiscal_year=excluded.fiscal_year,
            quarter=excluded.quarter,
            transcript_path=excluded.transcript_path,
            source_url=excluded.source_url,
            status=excluded.status,
            updated_at=CURRENT_TIMESTAMP
        """,
        {
            "case_id": row.get("case_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "fiscal_year": row.get("fiscal_year", ""),
            "quarter": row.get("quarter", ""),
            "transcript_path": row.get("transcript_path", ""),
            "source_url": row.get("source_url", ""),
            "status": row.get("status", "pending_review"),
        },
    )


def insert_review_record(connection: sqlite3.Connection, row: dict[str, Any]) -> None:
    upsert_corpus_case(
        connection,
        {
            "case_id": row.get("case_id", ""),
            "transcript_path": row.get("transcript_path", ""),
            "source_url": row.get("source_url", ""),
        },
    )
    payload = {
        "schema_version": row.get("schema_version", ""),
        "review_id": row.get("review_id", ""),
        "provenance_id": row.get("provenance_id", ""),
        "case_id": row.get("case_id", ""),
        "signal_type": row.get("signal_type", ""),
        "topic": row.get("topic", ""),
        "transcript_section": row.get("transcript_section", ""),
        "speaker_role": row.get("speaker_role", ""),
        "evidence_text": row.get("evidence_text", ""),
        "evidence_start_hint": row.get("evidence_start_hint", ""),
        "evidence_end_hint": row.get("evidence_end_hint", ""),
        "predicted_direction": row.get("predicted_direction", ""),
        "reviewer_action": row.get("reviewer_action", ""),
        "reviewer_notes": row.get("reviewer_notes", ""),
        "confidence": row.get("confidence", 0),
        "source_url": row.get("source_url", ""),
        "transcript_path": row.get("transcript_path", ""),
        "created_at": row.get("created_at", utc_now()),
        "reviewer_id": row.get("reviewer_id", ""),
        "assigned_reviewer_id": row.get("assigned_reviewer_id", ""),
        "review_status": row.get("review_status", "pending"),
        "reviewer_action_audit": row.get("reviewer_action_audit", ""),
        "disagreement_status": row.get("disagreement_status", "none"),
        "adjudication_notes": row.get("adjudication_notes", ""),
        "evidence_mismatch_class": row.get("evidence_mismatch_class", "none"),
    }
    connection.execute(
        """
        INSERT INTO review_records (
            review_id, schema_version, provenance_id, case_id, signal_type, topic, transcript_section, speaker_role,
            evidence_text, evidence_start_hint, evidence_end_hint, predicted_direction, reviewer_action,
            reviewer_notes, confidence, source_url, transcript_path, created_at, reviewer_id, assigned_reviewer_id,
            review_status, reviewer_action_audit, disagreement_status, adjudication_notes, evidence_mismatch_class
        )
        VALUES (
            :review_id, :schema_version, :provenance_id, :case_id, :signal_type, :topic, :transcript_section, :speaker_role,
            :evidence_text, :evidence_start_hint, :evidence_end_hint, :predicted_direction, :reviewer_action,
            :reviewer_notes, :confidence, :source_url, :transcript_path, :created_at, :reviewer_id, :assigned_reviewer_id,
            :review_status, :reviewer_action_audit, :disagreement_status, :adjudication_notes, :evidence_mismatch_class
        )
        ON CONFLICT(review_id) DO UPDATE SET
            reviewer_action=excluded.reviewer_action,
            reviewer_notes=excluded.reviewer_notes,
            reviewer_id=excluded.reviewer_id,
            assigned_reviewer_id=excluded.assigned_reviewer_id,
            review_status=excluded.review_status,
            reviewer_action_audit=excluded.reviewer_action_audit,
            disagreement_status=excluded.disagreement_status,
            adjudication_notes=excluded.adjudication_notes,
            evidence_mismatch_class=excluded.evidence_mismatch_class,
            updated_at=CURRENT_TIMESTAMP
        """,
        payload,
    )


def insert_gold_label(connection: sqlite3.Connection, row: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT OR REPLACE INTO gold_labels (
            id, schema_version, review_id, provenance_id, case_id, signal_type, direction, evidence_text,
            transcript_section, speaker_role, reviewer_id, source_url, transcript_path, evidence_mismatch_class
        )
        VALUES (
            :id, :schema_version, :review_id, :provenance_id, :case_id, :signal_type, :direction, :evidence_text,
            :transcript_section, :speaker_role, :reviewer_id, :source_url, :transcript_path, :evidence_mismatch_class
        )
        """,
        {
            "id": row.get("id", ""),
            "schema_version": row.get("schema_version", ""),
            "review_id": row.get("review_id", ""),
            "provenance_id": row.get("provenance_id", ""),
            "case_id": row.get("case_id", ""),
            "signal_type": row.get("signal_type") or row.get("signal_family", ""),
            "direction": row.get("direction", ""),
            "evidence_text": row.get("evidence_text") or row.get("text", ""),
            "transcript_section": row.get("transcript_section", ""),
            "speaker_role": row.get("speaker_role", ""),
            "reviewer_id": row.get("reviewer_id", ""),
            "source_url": row.get("source_url", ""),
            "transcript_path": row.get("transcript_path", ""),
            "evidence_mismatch_class": row.get("evidence_mismatch_class", "none"),
        },
    )


def insert_provenance_event(connection: sqlite3.Connection, event: dict[str, Any]) -> str:
    event_id = event.get("event_id") or stable_event_id(event.get("provenance_id"), event.get("review_id"), event.get("event_type"), json.dumps(event, sort_keys=True))
    connection.execute(
        """
        INSERT OR REPLACE INTO provenance_events (
            event_id, schema_version, provenance_id, review_id, case_id, event_type, source_path, source_url, payload_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            event.get("schema_version", ""),
            event.get("provenance_id", ""),
            event.get("review_id", ""),
            event.get("case_id", ""),
            event.get("event_type", ""),
            event.get("source_path", ""),
            event.get("source_url", ""),
            json.dumps(event.get("payload", {}), sort_keys=True),
            event.get("created_at", utc_now()),
        ),
    )
    return str(event_id)


def insert_evaluation_run(connection: sqlite3.Connection, run: dict[str, Any]) -> str:
    metrics = run.get("metrics", {})
    run_id = run.get("run_id") or "eval_" + hashlib.sha1(json.dumps(metrics, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    connection.execute(
        """
        INSERT OR REPLACE INTO evaluation_runs (
            run_id, schema_version, run_type, deterministic_output_path, gold_label_path, metrics_json, report_path,
            review_count, accepted_count, rejected_count, uncertain_count, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            run.get("schema_version", ""),
            run.get("run_type", ""),
            run.get("deterministic_output_path", ""),
            run.get("gold_label_path", ""),
            json.dumps(metrics, sort_keys=True),
            run.get("report_path", ""),
            int(run.get("review_count", 0)),
            int(run.get("accepted_count", 0)),
            int(run.get("rejected_count", 0)),
            int(run.get("uncertain_count", 0)),
            run.get("created_at", utc_now()),
        ),
    )
    return str(run_id)


def review_action_counts(connection: sqlite3.Connection) -> dict[str, int]:
    rows = connection.execute("SELECT review_status, COUNT(*) AS count FROM review_records GROUP BY review_status").fetchall()
    return {str(row["review_status"]): int(row["count"]) for row in rows}
