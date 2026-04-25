#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.signal_baseline import HUMAN_REVIEWED_LABELS_RELATIVE_PATH, SIGNAL_FAMILY_LABELS, load_supervised_examples


TRUE_VALUES = {"true", "yes", "y", "1"}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _render_report(status: dict[str, object]) -> str:
    lines = [
        "# Label Promotion Status",
        "",
        "This workflow promotes accepted candidate rows into the reviewed label dataset only after explicit human review.",
        "",
        f"- status: `{status['status']}`",
        f"- input_review_csv: `{status['input_review_csv']}`",
        f"- label_dataset_path: `{status['label_dataset_path']}`",
        f"- accepted_rows: `{status['accepted_rows']}`",
        f"- promoted_rows: `{status['promoted_rows']}`",
        f"- duplicate_rows_skipped: `{status['duplicate_rows_skipped']}`",
        "",
    ]
    if status["status"] == "blocked_no_accepted_rows":
        lines.extend(
            [
                "## Blocked Status",
                "",
                "- No candidate rows were marked accepted yet.",
                "- This is expected until a reviewer completes part of the candidate review CSV.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Promotion Notes",
                "",
                "- Existing labels were preserved.",
                "- Duplicate IDs and duplicate normalized text rows were skipped conservatively.",
                "- Promoted rows are marked with `label_source: human_reviewed_candidate_v1`.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote accepted candidate rows into the reviewed signal label dataset.")
    parser.add_argument(
        "--review-csv-path",
        default=str(ROOT / "data" / "nlp_research" / "signal_label_candidates_review.csv"),
    )
    parser.add_argument(
        "--labels-path",
        default=str(ROOT / HUMAN_REVIEWED_LABELS_RELATIVE_PATH),
    )
    parser.add_argument(
        "--status-out",
        default=str(ROOT / "data" / "nlp_research" / "label_promotion_status.json"),
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "label-promotion-status.md"),
    )
    args = parser.parse_args(argv)

    review_csv_path = Path(args.review_csv_path)
    labels_path = Path(args.labels_path)
    status_out = Path(args.status_out)
    report_out = Path(args.report_out)

    existing_rows = load_supervised_examples(labels_path)
    existing_ids = {row["id"] for row in existing_rows}
    existing_texts = {_normalize_text(row["text"]) for row in existing_rows}

    accepted_rows: list[dict[str, str]] = []
    if review_csv_path.exists():
        with review_csv_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                accepted = str(row.get("accepted", "")).strip().lower() in TRUE_VALUES
                reviewer_label = str(row.get("reviewer_label", "")).strip()
                if accepted and reviewer_label in SIGNAL_FAMILY_LABELS and str(row.get("text", "")).strip():
                    accepted_rows.append(row)

    promoted_rows: list[dict[str, object]] = []
    duplicate_rows_skipped = 0
    for row in accepted_rows:
        normalized_text = _normalize_text(row["text"])
        row_id = str(row["id"]).strip()
        if row_id in existing_ids or normalized_text in existing_texts:
            duplicate_rows_skipped += 1
            continue
        promoted = {
            "id": row_id,
            "source_file": str(row.get("source_file", "")).strip(),
            "domain": str(row.get("domain", "")).strip() or "unknown",
            "text": str(row["text"]).strip(),
            "signal_family": str(row["reviewer_label"]).strip(),
            "label_source": "human_reviewed_candidate_v1",
            "evidence_terms": [
                term.strip() for term in str(row.get("suggested_evidence_terms", "")).split(";") if term.strip()
            ],
            "rationale": str(row.get("reviewer_notes", "")).strip() or "Promoted from the reviewed candidate mining queue.",
            "pii_redacted": True,
            "notes": "Promoted from signal_label_candidates_review.csv after explicit human acceptance.",
        }
        promoted_rows.append(promoted)
        existing_ids.add(row_id)
        existing_texts.add(normalized_text)

    if promoted_rows:
        combined_rows = existing_rows + promoted_rows
        labels_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in combined_rows) + "\n",
            encoding="utf-8",
        )

    status = {
        "status": "ok" if promoted_rows else "blocked_no_accepted_rows",
        "input_review_csv": _display_path(review_csv_path),
        "label_dataset_path": _display_path(labels_path),
        "existing_rows_before": len(existing_rows),
        "accepted_rows": len(accepted_rows),
        "promoted_rows": len(promoted_rows),
        "duplicate_rows_skipped": duplicate_rows_skipped,
        "label_dataset_size_after": len(existing_rows) + len(promoted_rows),
    }
    status_out.parent.mkdir(parents=True, exist_ok=True)
    status_out.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(_render_report(status), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
