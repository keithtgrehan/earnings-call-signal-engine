#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.signal_baseline import (  # noqa: E402
    HUMAN_REVIEWED_LABELS_RELATIVE_PATH,
    SIGNAL_FAMILY_LABELS,
    load_supervised_examples,
)


REVIEW_PACKET_COLUMNS = [
    "id",
    "text",
    "current_label",
    "reviewer_label",
    "reviewer_confidence",
    "reviewer_notes",
    "evidence_terms",
    "rationale",
]


def build_review_rows(dataset_path: Path) -> list[dict[str, str]]:
    examples = load_supervised_examples(dataset_path)
    rows: list[dict[str, str]] = []
    for example in examples:
        rows.append(
            {
                "id": example["id"],
                "text": example["text"],
                "current_label": example["signal_family"],
                "reviewer_label": "",
                "reviewer_confidence": "",
                "reviewer_notes": "",
                "evidence_terms": "; ".join(example.get("evidence_terms") or []),
                "rationale": example.get("rationale", ""),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_PACKET_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _render_markdown(rows: list[dict[str, str]]) -> str:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["current_label"]].append(row)

    lines = [
        "# Signal Label Review Packet",
        "",
        "This packet is for a second human review pass over the seeded `signal_family` labels.",
        "",
        "Use it to fill in `reviewer_label`, `reviewer_confidence`, and `reviewer_notes` without editing the original dataset.",
        "",
        "Allowed labels:",
        "",
    ]
    for label in SIGNAL_FAMILY_LABELS:
        lines.append(f"- `{label}`")

    for label in SIGNAL_FAMILY_LABELS:
        lines.extend(
            [
                "",
                f"## {label}",
                "",
            ]
        )
        for row in grouped[label]:
            lines.extend(
                [
                    f"### {row['id']}",
                    "",
                    f"- text: {row['text']}",
                    f"- evidence_terms: {row['evidence_terms'] or 'none'}",
                    f"- rationale: {row['rationale'] or 'none'}",
                    "- reviewer_label: ",
                    "- reviewer_confidence: ",
                    "- reviewer_notes: ",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a reviewer packet for second-pass signal-family label review."
    )
    parser.add_argument(
        "--input-path",
        default=str(ROOT / HUMAN_REVIEWED_LABELS_RELATIVE_PATH),
        help="Path to the human-reviewed signal label JSONL file.",
    )
    parser.add_argument(
        "--csv-out",
        default=str(ROOT / "data" / "nlp_research" / "review_packets" / "signal_labels_review_packet.csv"),
        help="Path to the CSV review packet.",
    )
    parser.add_argument(
        "--markdown-out",
        default=str(ROOT / "data" / "nlp_research" / "review_packets" / "signal_labels_review_packet.md"),
        help="Path to the Markdown review packet.",
    )
    parser.add_argument(
        "--template-out",
        default=str(ROOT / "data" / "nlp_research" / "second_review_template.csv"),
        help="Path to the blank normalized second-review CSV template.",
    )
    args = parser.parse_args(argv)

    dataset_path = Path(args.input_path)
    rows = build_review_rows(dataset_path)
    csv_out = Path(args.csv_out)
    markdown_out = Path(args.markdown_out)
    template_out = Path(args.template_out)

    _write_csv(csv_out, rows)
    _write_csv(template_out, rows)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(_render_markdown(rows), encoding="utf-8")

    print(
        json.dumps(
            {
            "status": "ok",
            "row_count": len(rows),
            "csv_out": str(csv_out),
            "markdown_out": str(markdown_out),
            "template_out": str(template_out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
