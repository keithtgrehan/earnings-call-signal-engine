#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VALID_LABELS = {"risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral"}
VALID_DECISIONS = {"accept", "reject", "edit_label", "unclear", "skip", ""}
GOLD_DECISIONS = {"accept", "edit_label"}


@dataclass(frozen=True)
class ValidationResult:
    total_rows: int
    reviewed_rows: int
    accepted_rows: int
    rejected_rows: int
    unclear_rows: int
    skipped_rows: int
    unreviewed_rows: int
    invalid_rows: int
    accepted_gold_labels: int
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def clean(value: object) -> str:
    return str(value or "").strip()


def normalize_decision(value: object) -> str:
    decision = clean(value).lower()
    aliases = {"accepted": "accept", "edit": "edit_label", "rejected": "reject"}
    return aliases.get(decision, decision)


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_reviewed_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"reviewed batch not found: {display_path(path)}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate_rows(rows: list[dict[str, str]]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    counts: Counter[str] = Counter()
    duplicate_state: defaultdict[str, set[tuple[str, str]]] = defaultdict(set)
    accepted_gold_labels = 0

    for index, row in enumerate(rows, start=2):
        candidate_id = clean(row.get("candidate_id"))
        decision = normalize_decision(row.get("review_decision"))
        final_label = clean(row.get("final_label"))

        if not candidate_id:
            errors.append(f"row {index}: candidate_id is required")
        if decision not in VALID_DECISIONS:
            errors.append(f"row {index}: invalid review_decision `{decision}`")
        if final_label and final_label not in VALID_LABELS:
            errors.append(f"row {index}: invalid final_label `{final_label}`")
        if decision in GOLD_DECISIONS and not final_label:
            errors.append(f"row {index}: `{decision}` requires final_label")
        if decision in GOLD_DECISIONS and final_label in VALID_LABELS:
            accepted_gold_labels += 1

        if decision:
            counts[decision] += 1
        else:
            counts["unreviewed"] += 1

        if candidate_id and decision:
            duplicate_state[candidate_id].add((decision, final_label))

    for candidate_id, states in sorted(duplicate_state.items()):
        non_empty_states = {state for state in states if any(state)}
        if len(non_empty_states) > 1:
            errors.append(f"candidate_id `{candidate_id}` has conflicting duplicate review decisions: {sorted(non_empty_states)}")

    if not rows:
        warnings.append("reviewed batch is empty")
    if accepted_gold_labels == 0:
        warnings.append("no accepted gold labels are present; gold update will not add training data")

    reviewed_rows = counts["accept"] + counts["reject"] + counts["edit_label"] + counts["unclear"]
    return ValidationResult(
        total_rows=len(rows),
        reviewed_rows=reviewed_rows,
        accepted_rows=counts["accept"] + counts["edit_label"],
        rejected_rows=counts["reject"],
        unclear_rows=counts["unclear"],
        skipped_rows=counts["skip"],
        unreviewed_rows=counts["unreviewed"],
        invalid_rows=len(errors),
        accepted_gold_labels=accepted_gold_labels,
        errors=errors,
        warnings=warnings,
    )


def write_report(path: Path, result: ValidationResult, *, input_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Review Validation Report",
        "",
        f"- input: `{display_path(input_path)}`",
        f"- valid_for_gold_update: `{result.valid}`",
        f"- total_rows: `{result.total_rows}`",
        f"- reviewed_rows: `{result.reviewed_rows}`",
        f"- accepted_rows: `{result.accepted_rows}`",
        f"- accepted_gold_labels: `{result.accepted_gold_labels}`",
        f"- rejected_rows: `{result.rejected_rows}`",
        f"- unclear_rows: `{result.unclear_rows}`",
        f"- skipped_rows: `{result.skipped_rows}`",
        f"- unreviewed_rows: `{result.unreviewed_rows}`",
        f"- invalid_rows: `{result.invalid_rows}`",
        "",
    ]
    if result.errors:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in result.errors)
        lines.append("")
    if result.warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
        lines.append("")
    lines.append("Only rows with `review_decision` of `accept` or `edit_label` and a valid `final_label` are eligible for gold labels.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_result(result: ValidationResult, *, report_path: Path) -> None:
    print(f"reviewed rows: {result.reviewed_rows}")
    print(f"accepted rows: {result.accepted_rows}")
    print(f"rejected rows: {result.rejected_rows}")
    print(f"unclear rows: {result.unclear_rows}")
    print(f"skipped rows: {result.skipped_rows}")
    print(f"invalid rows: {result.invalid_rows}")
    print(f"valid for gold update: {result.valid}")
    print(f"report: {report_path}")


def validate_file(input_path: Path, report_path: Path) -> ValidationResult:
    try:
        rows = read_reviewed_csv(input_path)
    except FileNotFoundError as exc:
        result = ValidationResult(
            total_rows=0,
            reviewed_rows=0,
            accepted_rows=0,
            rejected_rows=0,
            unclear_rows=0,
            skipped_rows=0,
            unreviewed_rows=0,
            invalid_rows=1,
            accepted_gold_labels=0,
            errors=[str(exc)],
            warnings=[],
        )
    else:
        result = validate_rows(rows)
    write_report(report_path, result, input_path=input_path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a reviewed first-50 batch before gold-label import.")
    parser.add_argument("--input", default=str(ROOT / "data" / "labeling" / "reviewed_next_batch.csv"))
    parser.add_argument("--report", default=str(ROOT / "docs" / "labeling" / "review_validation_report.md"))
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    report_path = Path(args.report)
    result = validate_file(input_path, report_path)
    print_result(result, report_path=report_path)
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
