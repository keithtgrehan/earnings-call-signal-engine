from __future__ import annotations

from pathlib import Path
from typing import Any


INSTALL_GUIDANCE = 'Install review extras with: pip install -e ".[review]"'


class OptionalReviewDependencyError(RuntimeError):
    pass


def require_duckdb():
    try:
        import duckdb  # type: ignore
    except ModuleNotFoundError as exc:
        raise OptionalReviewDependencyError(f"DuckDB is required for review storage. {INSTALL_GUIDANCE}") from exc
    return duckdb


class ReviewStore:
    def __init__(self, path: Path | str = "data/review/runtime/review.duckdb") -> None:
        self.path = Path(path)
        self.duckdb = require_duckdb()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = self.duckdb.connect(str(self.path))
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        self.conn.execute("INSERT INTO schema_version SELECT 1, CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT 1 FROM schema_version)")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transcript_chunks (
                chunk_id VARCHAR PRIMARY KEY,
                case_id VARCHAR,
                source_file VARCHAR,
                section VARCHAR,
                speaker VARCHAR,
                chunk_index INTEGER,
                provenance_hash VARCHAR,
                text_hash VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weak_labels (
                chunk_id VARCHAR,
                case_id VARCHAR,
                label VARCHAR,
                confidence DOUBLE,
                rule_source VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS review_history (
                event_id VARCHAR,
                chunk_id VARCHAR,
                case_id VARCHAR,
                review_state VARCHAR,
                reviewer VARCHAR,
                labels VARCHAR,
                notes VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS export_history (
                export_id VARCHAR,
                output_path VARCHAR,
                row_count INTEGER,
                rejected_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_history (
                run_id VARCHAR,
                reviewed_count INTEGER,
                metrics_json VARCHAR,
                caveat VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def upsert_chunks(self, rows: list[dict[str, Any]]) -> int:
        for row in rows:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO transcript_chunks
                (chunk_id, case_id, source_file, section, speaker, chunk_index, provenance_hash, text_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    row.get("chunk_id"),
                    row.get("case_id"),
                    row.get("source_file"),
                    row.get("section"),
                    row.get("speaker"),
                    row.get("chunk_index"),
                    row.get("provenance_hash"),
                    row.get("provenance", {}).get("text_hash"),
                ],
            )
        return len(rows)

    def insert_weak_labels(self, rows: list[dict[str, Any]]) -> int:
        for row in rows:
            self.conn.execute(
                "INSERT INTO weak_labels (chunk_id, case_id, label, confidence, rule_source) VALUES (?, ?, ?, ?, ?)",
                [row.get("chunk_id"), row.get("case_id"), row.get("label"), row.get("confidence"), row.get("rule_source")],
            )
        return len(rows)

    def insert_review_history(self, rows: list[dict[str, Any]]) -> int:
        for row in rows:
            self.conn.execute(
                "INSERT INTO review_history (event_id, chunk_id, case_id, review_state, reviewer, labels, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    row.get("event_id"),
                    row.get("chunk_id"),
                    row.get("case_id"),
                    row.get("review_state"),
                    row.get("reviewer"),
                    ",".join(row.get("labels", [])) if isinstance(row.get("labels"), list) else row.get("labels"),
                    row.get("notes", ""),
                ],
            )
        return len(rows)

    def insert_export_history(self, *, export_id: str, output_path: str, row_count: int, rejected_count: int) -> None:
        self.conn.execute(
            "INSERT INTO export_history (export_id, output_path, row_count, rejected_count) VALUES (?, ?, ?, ?)",
            [export_id, output_path, row_count, rejected_count],
        )

    def insert_evaluation_history(self, *, run_id: str, reviewed_count: int, metrics_json: str, caveat: str) -> None:
        self.conn.execute(
            "INSERT INTO evaluation_history (run_id, reviewed_count, metrics_json, caveat) VALUES (?, ?, ?, ?)",
            [run_id, reviewed_count, metrics_json, caveat],
        )

    def close(self) -> None:
        self.conn.close()
