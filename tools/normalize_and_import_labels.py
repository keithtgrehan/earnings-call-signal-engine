#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from labeling_common import SIGNAL_LABELS, read_jsonl, review_decision, stable_id, write_jsonl  # noqa: E402

DEFAULT_SOURCES = [
    ROOT / "data" / "labeling" / "reviewed_labels.csv",
    ROOT / "data" / "nlp_research" / "human_reviewed_signal_labels.jsonl",
    ROOT / "data" / "gold_guidance_calls" / "labels.csv",
    ROOT / "data" / "gold_guidance_calls" / "draft_labels.csv",
    ROOT / "data" / "gold_guidance_calls" / "call_manifest.csv",
    ROOT / "data" / "gold_guidance_calls" / "official_source_manifest.csv",
    ROOT / "data" / "gold_guidance_calls" / "prior_quarter_sources.csv",
    ROOT / "data" / "gold_guidance_calls" / "transcript_inventory.csv",
    ROOT / "data" / "gold_guidance_calls" / "transcription_status.csv",
]

LABEL_ALIASES = {
    "risk_friction": "risk_friction",
    "risk": "risk_friction",
    "friction": "risk_friction",
    "opportunity_commitment": "opportunity_commitment",
    "opportunity": "opportunity_commitment",
    "commitment": "opportunity_commitment",
    "uncertainty_hedging": "uncertainty_hedging",
    "uncertainty": "uncertainty_hedging",
    "hedging": "uncertainty_hedging",
    "neutral": "neutral",
}

GUIDANCE_LABEL_MAP = {
    "raised": "opportunity_commitment",
    "maintained": "opportunity_commitment",
    "lowered": "risk_friction",
    "withdrawn": "risk_friction",
    "unclear": "uncertainty_hedging",
}


def read_source(path: Path) -> tuple[str, list[dict[str, Any]]]:
    if not path.exists():
        return "missing", []
    if path.suffix.lower() == ".jsonl":
        return "jsonl", read_jsonl(path)
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return "csv", [dict(row) for row in csv.DictReader(handle)]
    return "unsupported", []


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def text_from(row: dict[str, Any]) -> str:
    for key in ("text", "evidence_text", "matched_text", "segment_text", "utterance", "content"):
        value = str(row.get(key) or "").strip()
        if value:
            return " ".join(value.split())
    return ""


def case_id_from(row: dict[str, Any], source_path: Path) -> str:
    for key in ("case_id", "call_id", "source_call_id", "conversation_id", "source_file", "source_path"):
        value = str(row.get(key) or "").strip()
        if value:
            return Path(value).stem
    return source_path.stem


def normalize_label(row: dict[str, Any]) -> tuple[str, str]:
    for key in ("signal_family", "final_label", "label", "weak_label"):
        raw = str(row.get(key) or "").strip().lower().replace("-", "_").replace(" ", "_")
        if raw in LABEL_ALIASES:
            return LABEL_ALIASES[raw], f"{key}:{raw}"
    guidance = str(row.get("guidance_change_label") or "").strip().lower().replace("-", "_").replace(" ", "_")
    if guidance in GUIDANCE_LABEL_MAP:
        return GUIDANCE_LABEL_MAP[guidance], f"guidance_change_label:{guidance}"
    return "", "no_valid_label"


def row_id(row: dict[str, Any], *, source_path: Path, case_id: str, text: str, label: str) -> str:
    for key in ("id", "candidate_id", "label_id"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    if row.get("guidance_change_label"):
        digest = hashlib.sha1(f"{source_path}|{case_id}|{text}|{label}".encode("utf-8")).hexdigest()[:12]
        return f"guidance_{case_id}_{digest}"
    return stable_id(str(source_path), case_id, text, label)


def is_reviewed_accept(row: dict[str, Any], schema: str) -> bool:
    if schema == "reviewed_csv":
        return review_decision(row) == "accepted"
    if schema in {"human_reviewed_jsonl", "guidance_labels_csv"}:
        return True
    return False


def detect_schema(path: Path, rows: list[dict[str, Any]]) -> str:
    fields = set(rows[0]) if rows else set()
    if {"review_decision", "final_label", "candidate_id"} <= fields:
        return "reviewed_csv"
    if {"signal_family", "text"} <= fields:
        return "human_reviewed_jsonl"
    if {"guidance_change_label", "evidence_text"} <= fields:
        return "guidance_labels_csv"
    if path.exists():
        return "metadata_or_unsupported"
    return "missing"


def normalize_row(row: dict[str, Any], *, source_path: Path, schema: str, row_number: int) -> tuple[dict[str, Any] | None, str, str]:
    if not is_reviewed_accept(row, schema):
        return None, "not_imported", "row is not an accepted human/guidance label"
    text = text_from(row)
    label, label_note = normalize_label(row)
    case_id = case_id_from(row, source_path)
    if not text:
        return None, "rejected", "missing text/evidence span"
    if label not in SIGNAL_LABELS:
        return None, "rejected", f"invalid or unmapped label ({label_note})"
    item_id = row_id(row, source_path=source_path, case_id=case_id, text=text, label=label)
    canonical = {
        "id": item_id,
        "candidate_id": str(row.get("candidate_id") or item_id),
        "case_id": case_id,
        "text": text,
        "signal_family": label,
        "label_source": "normalized_import",
        "source_file": display_path(source_path),
        "source_schema": schema,
        "source_row": row_number,
        "metadata": {
            "label_mapping": label_note,
            "original_label": str(row.get("signal_family") or row.get("final_label") or row.get("label") or row.get("guidance_change_label") or ""),
            "confidence": str(row.get("confidence") or row.get("label_confidence") or ""),
            "notes": str(row.get("reviewer_notes") or row.get("notes") or row.get("rationale") or ""),
            "evidence_start": str(row.get("evidence_start") or ""),
            "evidence_end": str(row.get("evidence_end") or ""),
            "ticker": str(row.get("ticker") or ""),
            "company": str(row.get("company") or ""),
            "quarter": str(row.get("quarter") or ""),
        },
    }
    return canonical, "valid", "normalized"


def dedupe_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("case_id") or ""),
        " ".join(str(row.get("text") or "").lower().split()),
        str(row.get("signal_family") or ""),
    )


def import_sources(sources: list[Path], gold_path: Path, summary_path: Path) -> dict[str, Any]:
    existing = read_jsonl(gold_path)
    existing_ids = {str(row.get("id") or row.get("candidate_id") or "") for row in existing}
    existing_keys = {dedupe_key(row) for row in existing}
    imported: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    source_summaries: list[dict[str, Any]] = []

    for source in sources:
        source_type, rows = read_source(source)
        schema = detect_schema(source, rows)
        stats = {"source": display_path(source), "source_type": source_type, "schema": schema, "rows_found": len(rows), "rows_valid": 0, "rows_imported": 0, "rows_rejected": 0}
        for index, row in enumerate(rows, start=2 if source.suffix.lower() == ".csv" else 1):
            canonical, status, reason = normalize_row(row, source_path=source, schema=schema, row_number=index)
            if status != "valid" or canonical is None:
                stats["rows_rejected"] += 1
                rejected.append({"source": stats["source"], "row": str(index), "status": status, "reason": reason})
                continue
            stats["rows_valid"] += 1
            item_id = str(canonical.get("id") or canonical.get("candidate_id") or "")
            key = dedupe_key(canonical)
            if item_id in existing_ids or key in existing_keys:
                stats["rows_rejected"] += 1
                rejected.append({"source": stats["source"], "row": str(index), "status": "duplicate", "reason": "duplicate id or case/text/label"})
                continue
            imported.append(canonical)
            existing_ids.add(item_id)
            existing_keys.add(key)
            stats["rows_imported"] += 1
        source_summaries.append(stats)

    if imported:
        write_jsonl(gold_path, [*existing, *imported])
    write_summary(summary_path, source_summaries, imported, rejected, gold_path)
    return {"sources": source_summaries, "imported": imported, "rejected": rejected, "gold_total": len(read_jsonl(gold_path))}


def write_summary(path: Path, source_summaries: list[dict[str, Any]], imported: list[dict[str, Any]], rejected: list[dict[str, str]], gold_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Label Import Summary",
        "",
        f"- gold_output: `{display_path(gold_path)}`",
        f"- rows_imported: `{len(imported)}`",
        f"- rows_rejected_or_skipped: `{len(rejected)}`",
        "",
        "## Sources",
        "",
    ]
    for item in source_summaries:
        lines.append(
            f"- `{item['source']}` schema=`{item['schema']}` found=`{item['rows_found']}` valid=`{item['rows_valid']}` imported=`{item['rows_imported']}` rejected=`{item['rows_rejected']}`"
        )
    lines.extend(["", "## Imported Rows", ""])
    if imported:
        for row in imported[:80]:
            lines.append(f"- `{row['id']}` case=`{row['case_id']}` label=`{row['signal_family']}` source=`{row['source_file']}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Rejected / Skipped Rows", ""])
    for row in rejected[:120]:
        lines.append(f"- `{row['source']}` row `{row['row']}`: {row['status']} - {row['reason']}")
    if len(rejected) > 120:
        lines.append(f"- ... {len(rejected) - 120} additional rejected/skipped rows omitted from summary view.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize existing label sources and append valid rows to canonical gold labels.")
    parser.add_argument("sources", nargs="*", help="Optional source files. Defaults to known label sources.")
    parser.add_argument("--gold-out", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--summary-out", default=str(ROOT / "reports" / "label_import_summary.md"))
    args = parser.parse_args(argv)
    sources = [Path(item) for item in args.sources] if args.sources else DEFAULT_SOURCES
    result = import_sources(sources, Path(args.gold_out), Path(args.summary_out))
    print(json.dumps({"sources": result["sources"], "imported": len(result["imported"]), "rejected": len(result["rejected"]), "gold_total": result["gold_total"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
