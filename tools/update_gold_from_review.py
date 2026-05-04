#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from labeling_common import read_jsonl  # noqa: E402
from train_text_signal_model import training_gate, write_error_analysis, write_model_card  # noqa: E402
from validate_reviewed_batch import read_reviewed_csv, validate_file, validate_rows  # noqa: E402


def next_threshold(count: int) -> str:
    if count < 20:
        return f"{20 - count} more gold labels for preliminary evaluation"
    if count < 50:
        return f"{50 - count} more gold labels for guarded baseline training"
    if count < 100:
        return f"{100 - count} more gold labels for broader preliminary metrics"
    if count < 500:
        return f"{500 - count} more gold labels for train/dev/test split"
    return "remote compute is still gated by benchmark quality and training configs"


def run_tool(script: str, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(TOOLS / script), *(args or [])]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result


def write_no_gold_status(*, reviewed_rows: int, accepted: int, rejected: int, unclear: int, skipped: int) -> None:
    status = ROOT / "docs" / "labeling" / "gold_label_status.md"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        "\n".join(
            [
                "# Gold Label Status",
                "",
                f"- reviewed_rows: `{reviewed_rows}`",
                f"- gold_labels_added_from_latest_review: `{accepted}`",
                f"- rejected_rows: `{rejected}`",
                f"- unclear_rows: `{unclear}`",
                f"- skipped_rows: `{skipped}`",
                "",
                "No accepted reviewed labels were present, so `data/gold/gold_labels.jsonl` was not updated.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_benchmark_skip(count: int) -> None:
    path = ROOT / "docs" / "evaluation" / "benchmark_status.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "gold_labels": count,
        "gate": "insufficient_data" if count < 20 else "preliminary_metrics_only",
        "metrics_computed": False,
    }
    path.write_text(
        "\n".join(
            [
                "# Benchmark Status",
                "",
                f"- gold_labels: `{count}`",
                f"- gate: `{payload['gate']}`",
                "- metrics_computed: `False`",
                "",
                "Metrics are gated until there are at least 20 gold labels.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_training_skip(count: int) -> None:
    summary: dict[str, Any] = {
        "gold_labels": count,
        "gate": training_gate(count),
        "training_ran": False,
        "validity": "invalid_for_training_less_than_50_gold_labels",
        "models": {},
        "model_path": None,
    }
    write_model_card(ROOT / "docs" / "model_eval" / "text_signal_model_card.md", summary)
    write_error_analysis(ROOT / "docs" / "model_eval" / "text_signal_error_analysis.md", [])


def total_gold_labels() -> int:
    return len(read_jsonl(ROOT / "data" / "gold" / "gold_labels.jsonl"))


def update_gold(input_path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    report_path = ROOT / "docs" / "labeling" / "review_validation_report.md"
    if dry_run:
        try:
            validation = validate_rows(read_reviewed_csv(input_path))
        except FileNotFoundError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        validation = validate_file(input_path, report_path)

    summary: dict[str, Any] = {
        "reviewed_rows": validation.reviewed_rows,
        "accepted_gold_labels": validation.accepted_gold_labels,
        "rejected_rows": validation.rejected_rows,
        "unclear_rows": validation.unclear_rows,
        "skipped_rows": validation.skipped_rows,
        "total_gold_labels": total_gold_labels(),
        "evaluation_ran": False,
        "training_ran": False,
        "dry_run": dry_run,
        "outputs": {
            "review_validation_report": str(report_path),
            "reviewed_labels": str(ROOT / "data" / "labeling" / "reviewed_labels.csv"),
            "gold_labels": str(ROOT / "data" / "gold" / "gold_labels.jsonl"),
            "gold_status": str(ROOT / "docs" / "labeling" / "gold_label_status.md"),
            "benchmark_status": str(ROOT / "docs" / "evaluation" / "benchmark_status.md"),
            "model_card": str(ROOT / "docs" / "model_eval" / "text_signal_model_card.md"),
        },
    }

    if not validation.valid:
        raise SystemExit("review validation failed; gold labels were not modified")

    if dry_run:
        summary["next_threshold"] = next_threshold(summary["total_gold_labels"])
        return summary

    if validation.accepted_gold_labels == 0:
        write_no_gold_status(
            reviewed_rows=validation.reviewed_rows,
            accepted=validation.accepted_gold_labels,
            rejected=validation.rejected_rows,
            unclear=validation.unclear_rows,
            skipped=validation.skipped_rows,
        )
        write_benchmark_skip(summary["total_gold_labels"])
        write_training_skip(summary["total_gold_labels"])
        summary["next_threshold"] = next_threshold(summary["total_gold_labels"])
        return summary

    import_result = run_tool("import_reviewed_labels.py", ["--input", str(input_path)])
    if import_result.returncode != 0:
        raise SystemExit("import reviewed labels failed")

    build_result = run_tool("build_gold_labels.py")
    if build_result.returncode != 0:
        raise SystemExit("build gold labels failed")

    coverage_result = run_tool("check_gold_coverage.py")
    if coverage_result.returncode != 0:
        print("gold coverage reported a gated warning", file=sys.stderr)

    evaluate_result = run_tool("evaluate_gold_labels.py")
    summary["evaluation_ran"] = True
    if evaluate_result.returncode != 0:
        print("evaluation reported a gated warning", file=sys.stderr)

    summary["total_gold_labels"] = total_gold_labels()
    if summary["total_gold_labels"] >= 50:
        train_result = run_tool("train_text_signal_model.py")
        summary["training_ran"] = train_result.returncode == 0
    else:
        write_training_skip(summary["total_gold_labels"])

    summary["next_threshold"] = next_threshold(summary["total_gold_labels"])
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print(f"reviewed rows: {summary['reviewed_rows']}")
    print(f"accepted gold labels: {summary['accepted_gold_labels']}")
    print(f"rejected rows: {summary['rejected_rows']}")
    print(f"unclear rows: {summary['unclear_rows']}")
    print(f"skipped rows: {summary['skipped_rows']}")
    print(f"total gold labels: {summary['total_gold_labels']}")
    print(f"evaluation ran: {summary['evaluation_ran']}")
    print(f"training ran: {summary['training_ran']}")
    print(f"next threshold: {summary['next_threshold']}")
    print("output paths:")
    for name, path in summary["outputs"].items():
        print(f"  {name}: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a reviewed batch and update gold labels through existing guarded tools.")
    parser.add_argument("--input", default=str(ROOT / "data" / "labeling" / "reviewed_next_batch.csv"))
    parser.add_argument("--dry-run", action="store_true", help="Validate and print planned actions without updating gold labels.")
    args = parser.parse_args(argv)

    summary = update_gold(Path(args.input), dry_run=args.dry_run)
    print_summary(summary)
    if args.dry_run:
        print("dry-run summary:")
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
