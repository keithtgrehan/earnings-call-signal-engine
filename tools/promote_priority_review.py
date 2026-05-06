#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from priority_review_common import (  # noqa: E402
    GOLD_PATH,
    LABELS,
    PACKET_CSV,
    gold_fingerprints,
    norm_text,
    read_csv,
    read_jsonl,
    row_label,
    write_jsonl,
)

REPORT_PATH = ROOT / "reports" / "gold_label_growth_status.md"


def decision(row: dict[str, str]) -> str:
    return str(row.get("reviewer_decision") or "").strip().lower()


def selected_label(row: dict[str, str]) -> str:
    return str(row.get("corrected_label") or row.get("predicted_label") or "").strip()


def canonical_row(row: dict[str, str], label: str, reviewer: str) -> dict[str, Any]:
    review_id = str(row.get("review_id") or "").strip()
    case_id = str(row.get("case_id") or "").strip()
    text = str(row.get("evidence_text") or "").strip()
    return {
        "id": f"priority_{review_id}",
        "candidate_id": review_id,
        "case_id": case_id,
        "text": text,
        "signal_family": label,
        "label_source": "human_reviewed_priority_packet",
        "source_file": row.get("source_path") or str(PACKET_CSV.relative_to(ROOT)),
        "source_case_id": case_id,
        "reviewer": reviewer,
        "review_id": review_id,
        "provenance_quality": "high",
        "requires_manual_review": False,
        "metadata": {
            "ticker": row.get("ticker") or "",
            "fiscal_period": row.get("fiscal_period") or "",
            "section": row.get("section") or "",
            "speaker": row.get("speaker") or "",
            "reviewer_notes": row.get("reviewer_notes") or "",
            "predicted_label": row.get("predicted_label") or "",
            "corrected_label": row.get("corrected_label") or "",
            "trigger_terms": row.get("trigger_terms") or "",
            "deterministic_confidence": row.get("deterministic_confidence") or "",
            "ml_prediction_if_available": row.get("ml_prediction_if_available") or "",
            "review_priority_reason": row.get("review_priority_reason") or "",
            "import_method": "priority_review_packet_accept_only",
        },
    }


def validate_packet_row(row: dict[str, str]) -> tuple[bool, str]:
    if decision(row) != "accept":
        return False, "not_accepted"
    if not str(row.get("review_id") or "").strip():
        return False, "missing_review_id"
    if not str(row.get("case_id") or "").strip():
        return False, "missing_case_id"
    if not str(row.get("evidence_text") or "").strip():
        return False, "missing_evidence_text"
    if selected_label(row) not in LABELS:
        return False, "invalid_label"
    return True, ""


def write_report(
    *,
    previous_rows: list[dict[str, Any]],
    imported_rows: list[dict[str, Any]],
    skipped_duplicates: int,
    rejected_count: int,
    unclear_count: int,
    blank_count: int,
    invalid_reasons: Counter[str],
    dry_run: bool,
    report_path: Path = REPORT_PATH,
) -> None:
    before_counts = Counter(row_label(row) for row in previous_rows if row_label(row))
    after_rows = [*previous_rows, *imported_rows]
    after_counts = Counter(row_label(row) for row in after_rows if row_label(row))
    per_call = Counter(str(row.get("case_id") or "") for row in imported_rows)
    new_count = len(after_rows)
    lines = [
        "# Gold Label Growth Status",
        "",
        f"- dry_run: `{dry_run}`",
        f"- previous_gold_count: `{len(previous_rows)}`",
        f"- accepted_imported_count: `{len(imported_rows)}`",
        f"- duplicate_skipped_count: `{skipped_duplicates}`",
        f"- rejected_count: `{rejected_count}`",
        f"- unclear_count: `{unclear_count}`",
        f"- blank_count: `{blank_count}`",
        f"- invalid_count: `{sum(invalid_reasons.values())}`",
        f"- new_gold_count: `{new_count}`",
        f"- labels_needed_to_reach_100: `{max(0, 100 - new_count)}`",
        f"- labels_needed_to_reach_250: `{max(0, 250 - new_count)}`",
        "",
        "## Invalid Reasons",
        "",
        *[f"- `{reason}`: {count}" for reason, count in sorted(invalid_reasons.items())],
        "",
        "## Label Distribution Before",
        "",
        *[f"- `{label}`: {before_counts.get(label, 0)}" for label in LABELS],
        "",
        "## Label Distribution After",
        "",
        *[f"- `{label}`: {after_counts.get(label, 0)}" for label in LABELS],
        "",
        "## Accepted Labels By Call",
        "",
        *[f"- `{case_id}`: {count}" for case_id, count in sorted(per_call.items())],
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def promote(packet_path: Path, gold_path: Path, *, dry_run: bool, reviewer: str, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    packet_rows = read_csv(packet_path)
    gold_rows = read_jsonl(gold_path)
    fingerprints = gold_fingerprints(gold_rows)
    imported: list[dict[str, Any]] = []
    skipped_duplicates = 0
    invalid_reasons: Counter[str] = Counter()
    decision_counts = Counter(decision(row) or "blank" for row in packet_rows)
    for row in packet_rows:
        valid, reason = validate_packet_row(row)
        if not valid:
            if reason != "not_accepted":
                invalid_reasons[reason] += 1
            continue
        label = selected_label(row)
        case_id = str(row.get("case_id") or "").strip()
        text = norm_text(str(row.get("evidence_text") or ""))
        if (case_id, text, label) in fingerprints or ("", text, label) in fingerprints:
            skipped_duplicates += 1
            continue
        canonical = canonical_row(row, label, reviewer)
        imported.append(canonical)
        fingerprints.add((case_id, text, label))
        fingerprints.add(("", text, label))
    if imported and not dry_run:
        write_jsonl(gold_path, [*gold_rows, *imported])
    write_report(
        previous_rows=gold_rows,
        imported_rows=imported,
        skipped_duplicates=skipped_duplicates,
        rejected_count=decision_counts.get("reject", 0),
        unclear_count=decision_counts.get("unclear", 0),
        blank_count=decision_counts.get("blank", 0),
        invalid_reasons=invalid_reasons,
        dry_run=dry_run,
        report_path=report_path,
    )
    return {
        "status": "ok",
        "dry_run": dry_run,
        "previous_gold_count": len(gold_rows),
        "accepted_imported_count": len(imported),
        "duplicate_skipped_count": skipped_duplicates,
        "new_gold_count": len(gold_rows) + len(imported),
        "labels_needed_to_reach_100": max(0, 100 - (len(gold_rows) + len(imported))),
        "report": str(report_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote accepted priority-review rows into canonical gold labels.")
    parser.add_argument("--packet", default=str(PACKET_CSV))
    parser.add_argument("--gold", default=str(GOLD_PATH))
    parser.add_argument("--reviewer", default="Keith")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    payload = promote(Path(args.packet), Path(args.gold), dry_run=args.dry_run, reviewer=args.reviewer)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
