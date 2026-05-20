from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .chunking import stable_hash
from .suggestions import SIGNALS


REVIEW_STATES = ["pending", "suggested", "reviewed", "approved", "rejected", "exported"]
EXPORTABLE_STATES = {"reviewed", "approved"}


class ReviewExportError(ValueError):
    pass


@dataclass(frozen=True)
class GoldLabel:
    case_id: str
    chunk_id: str
    text: str
    labels: list[str]
    source: str
    reviewer: str
    review_timestamp: str
    metadata: dict[str, Any]
    provenance: dict[str, Any]

    def to_record(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "labels": self.labels,
            "source": self.source,
            "reviewer": self.reviewer,
            "review_timestamp": self.review_timestamp,
            "metadata": self.metadata,
            "provenance": self.provenance,
        }


def dedup_key(row: dict[str, Any]) -> str:
    labels = row.get("labels") or []
    label = "|".join(sorted(str(item) for item in labels))
    return stable_hash(row.get("case_id"), row.get("chunk_id"), label, stable_hash(str(row.get("text") or ""), length=32), length=32)


def validate_reviewed_row(row: dict[str, Any]) -> GoldLabel:
    state = str(row.get("review_state") or row.get("status") or "").strip().lower()
    if state not in EXPORTABLE_STATES:
        raise ReviewExportError(f"row is not explicitly reviewed/approved: {state or 'missing'}")
    labels = row.get("labels") or row.get("reviewed_labels") or row.get("annotation") or []
    if isinstance(labels, str):
        labels = [item.strip() for item in labels.split(";") if item.strip()]
    labels = sorted(set(str(label) for label in labels if str(label) in SIGNALS))
    if not labels:
        raise ReviewExportError("reviewed row has no valid labels")
    case_id = str(row.get("case_id") or row.get("metadata", {}).get("case_id") or "")
    chunk_id = str(row.get("chunk_id") or row.get("metadata", {}).get("chunk_id") or row.get("external_id") or "")
    text = str(row.get("text") or "")
    if not case_id or not chunk_id or not text:
        raise ReviewExportError("reviewed row must include case_id, chunk_id, and text")
    reviewer = str(row.get("reviewer") or row.get("reviewer_id") or "")
    if not reviewer:
        raise ReviewExportError("reviewed row must include reviewer metadata")
    timestamp = str(row.get("review_timestamp") or row.get("updated_at") or datetime.now(timezone.utc).isoformat())
    metadata = dict(row.get("metadata") or {})
    provenance = dict(row.get("provenance") or {})
    provenance.setdefault("chunk_id", chunk_id)
    provenance.setdefault("case_id", case_id)
    provenance.setdefault("source", row.get("source") or "argilla_review")
    provenance.setdefault("text_hash", stable_hash(text, length=32))
    return GoldLabel(
        case_id=case_id,
        chunk_id=chunk_id,
        text=text,
        labels=labels,
        source=str(row.get("source") or "argilla_review"),
        reviewer=reviewer,
        review_timestamp=timestamp,
        metadata=metadata,
        provenance=provenance,
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def export_gold_labels(
    reviewed_rows: Iterable[dict[str, Any]],
    *,
    existing_rows: Iterable[dict[str, Any]] | None = None,
    mode: str = "merge",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if mode not in {"new", "append", "merge"}:
        raise ValueError("mode must be one of: new, append, merge")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in reviewed_rows:
        try:
            accepted.append(validate_reviewed_row(row).to_record())
        except ReviewExportError as exc:
            rejected.append({"row": row, "reason": str(exc)})
    if mode == "new":
        return accepted, rejected
    merged: dict[str, dict[str, Any]] = {}
    for row in existing_rows or []:
        merged[dedup_key(row)] = dict(row)
    for row in accepted:
        key = dedup_key(row)
        if mode == "append" and key in merged:
            continue
        merged[key] = row
    return list(merged.values()), rejected
