#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.emotion_benchmark import inter_rater_agreement_percent  # noqa: E402
from signal_engine.signal_baseline import SIGNAL_FAMILY_LABELS  # noqa: E402


ALLOWED_LABELS = set(SIGNAL_FAMILY_LABELS)


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def _blocked_payload(reason: str, *, input_path: Path) -> dict[str, Any]:
    return {
        "status": "blocked",
        "input_path": str(input_path),
        "raw_agreement_percent": None,
        "cohen_kappa": None,
        "reviewed_example_count": 0,
        "reason": reason,
        "disagreements": [],
        "per_class_disagreement_counts": {label: 0 for label in SIGNAL_FAMILY_LABELS},
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Label Agreement Status",
        "",
        f"- status: `{payload['status']}`",
        "",
    ]
    if payload["status"] != "ok":
        lines.extend(
            [
                "## Current State",
                "",
                payload["reason"],
                "",
                "Inter-rater agreement cannot be measured yet because second-review labels are still missing.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Agreement Summary",
            "",
            f"- reviewed_example_count: `{payload['reviewed_example_count']}`",
            f"- raw_agreement_percent: `{payload['raw_agreement_percent']:.2f}`",
            f"- cohen_kappa: `{payload['cohen_kappa'] if payload['cohen_kappa'] is not None else 'unavailable'}`",
            "",
            "## Per-Class Disagreement Counts",
            "",
            "| label | disagreements |",
            "| --- | --- |",
        ]
    )
    for label in SIGNAL_FAMILY_LABELS:
        lines.append(f"| {label} | {payload['per_class_disagreement_counts'].get(label, 0)} |")

    lines.extend(
        [
            "",
            "## Disagreement Table",
            "",
            "| id | current_label | reviewer_label | text |",
            "| --- | --- | --- | --- |",
        ]
    )
    if payload["disagreements"]:
        for row in payload["disagreements"]:
            lines.append(
                f"| {row['id']} | {row['current_label']} | {row['reviewer_label']} | {row['text']} |"
            )
    else:
        lines.append("| none | - | - | No disagreements in the current reviewed subset. |")
    return "\n".join(lines).rstrip() + "\n"


def evaluate_agreement(rows: list[dict[str, str]], *, input_path: Path) -> dict[str, Any]:
    if not rows:
        return _blocked_payload(
            "No second-review CSV is available yet. Run the review packet workflow and add reviewer labels first.",
            input_path=input_path,
        )

    reviewed_rows = [row for row in rows if row.get("reviewer_label")]
    if not reviewed_rows:
        return _blocked_payload(
            "No reviewer_label values are filled in yet, so inter-rater agreement cannot be measured.",
            input_path=input_path,
        )

    for row in reviewed_rows:
        if row["current_label"] not in ALLOWED_LABELS:
            raise ValueError(f"Invalid current_label '{row['current_label']}' for row {row.get('id')}")
        if row["reviewer_label"] not in ALLOWED_LABELS:
            raise ValueError(f"Invalid reviewer_label '{row['reviewer_label']}' for row {row.get('id')}")

    current_labels = [row["current_label"] for row in reviewed_rows]
    reviewer_labels = [row["reviewer_label"] for row in reviewed_rows]
    disagreements = [
        {
            "id": row.get("id", ""),
            "current_label": row["current_label"],
            "reviewer_label": row["reviewer_label"],
            "text": row.get("text", ""),
        }
        for row in reviewed_rows
        if row["current_label"] != row["reviewer_label"]
    ]
    per_class_disagreement_counts = {
        label: sum(
            1
            for row in reviewed_rows
            if row["current_label"] == label and row["current_label"] != row["reviewer_label"]
        )
        for label in SIGNAL_FAMILY_LABELS
    }
    kappa = None
    try:
        from sklearn.metrics import cohen_kappa_score

        kappa = round(float(cohen_kappa_score(current_labels, reviewer_labels, labels=list(SIGNAL_FAMILY_LABELS))), 4)
    except Exception:  # pragma: no cover - optional dependency/environment differences
        kappa = None

    return {
        "status": "ok",
        "input_path": str(input_path),
        "reviewed_example_count": len(reviewed_rows),
        "reviewer_label_counts": dict(Counter(reviewer_labels)),
        "raw_agreement_percent": round(inter_rater_agreement_percent(current_labels, reviewer_labels), 2),
        "cohen_kappa": kappa,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "per_class_disagreement_counts": per_class_disagreement_counts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate second-review label agreement when reviewer labels are available."
    )
    parser.add_argument(
        "--input-csv",
        default=str(ROOT / "data" / "nlp_research" / "second_review_template.csv"),
        help="Path to the normalized second-review CSV.",
    )
    parser.add_argument(
        "--status-out",
        default=str(ROOT / "data" / "nlp_research" / "label_agreement_status.json"),
        help="Path to the JSON agreement status output.",
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "label-agreement-status.md"),
        help="Path to the Markdown agreement report.",
    )
    args = parser.parse_args(argv)

    input_csv = Path(args.input_csv)
    rows = _read_rows(input_csv)
    payload = evaluate_agreement(rows, input_path=input_csv)

    status_out = Path(args.status_out)
    report_out = Path(args.report_out)
    _write_json(status_out, payload)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(_render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "reviewed_example_count": payload["reviewed_example_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
