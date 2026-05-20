from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

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
    confidence REAL NOT NULL DEFAULT 0,
    source_url TEXT,
    transcript_path TEXT,
    created_at TEXT NOT NULL,
    reviewer_id TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES corpus_cases(case_id)
);

CREATE TABLE IF NOT EXISTS gold_labels (
    id TEXT PRIMARY KEY,
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
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES review_records(review_id),
    FOREIGN KEY (case_id) REFERENCES corpus_cases(case_id)
);

CREATE TABLE IF NOT EXISTS provenance_events (
    event_id TEXT PRIMARY KEY,
    provenance_id TEXT NOT NULL,
    case_id TEXT,
    event_type TEXT NOT NULL,
    source_path TEXT,
    source_url TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id TEXT PRIMARY KEY,
    run_type TEXT NOT NULL,
    deterministic_output_path TEXT,
    gold_label_path TEXT,
    metrics_json TEXT NOT NULL,
    report_path TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


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
    connection.commit()
    return connection


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
    upsert_corpus_case(connection, {"case_id": row.get("case_id", ""), "transcript_path": row.get("transcript_path", ""), "source_url": row.get("source_url", "")})
    connection.execute(
        """
        INSERT OR REPLACE INTO review_records (
            review_id, provenance_id, case_id, signal_type, topic, transcript_section, speaker_role,
            evidence_text, evidence_start_hint, evidence_end_hint, predicted_direction, reviewer_action,
            reviewer_notes, confidence, source_url, transcript_path, created_at, reviewer_id, review_status
        )
        VALUES (
            :review_id, :provenance_id, :case_id, :signal_type, :topic, :transcript_section, :speaker_role,
            :evidence_text, :evidence_start_hint, :evidence_end_hint, :predicted_direction, :reviewer_action,
            :reviewer_notes, :confidence, :source_url, :transcript_path, :created_at, :reviewer_id, :review_status
        )
        """,
        row,
    )
