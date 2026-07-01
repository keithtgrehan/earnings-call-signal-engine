#!/usr/bin/env python3
"""Build metadata-only weak review assistance for first100 candidates."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_public_model_assist_registry import DEFAULT_REGISTRY, validate_registry  # noqa: E402

DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
DEFAULT_CALIBRATION = ROOT / "data" / "review" / "staging" / "first100_calibration_batch_001.jsonl"
DEFAULT_OUT = ROOT / "reports" / "review" / "first100_weak_model_assist.csv"
DEFAULT_REPORT = ROOT / "reports" / "review" / "first100_weak_model_assist.md"

ASSIST_FIELDS = [
    "candidate_id",
    "case_id",
    "ticker",
    "fiscal_period",
    "existing_suggested_label",
    "weak_model_suggested_label",
    "weak_model_confidence",
    "assist_method",
    "disagreement_flag",
    "review_priority",
    "reason_code",
    "allowed_for_final_adjudication",
    "gold_created",
    "training_performed",
    "raw_text_used",
    "raw_text_returned",
]
HIGH_PRIORITY_LABELS = {"guidance_revision", "answer_shift", "management_hedging", "uncertainty", "analyst_pressure"}
MEDIUM_PRIORITY_LABELS = {"guidance_statement", "reassurance"}
LOW_PRIORITY_LABELS = {"neutral/no_signal"}
PROVENANCE_FIELDS = ("source_sha256", "normalized_transcript_hash", "provenance_hash")
RULE_LABEL_HINTS = [
    ("guidance_revision", "guidance_revision"),
    ("guidance_statement", "guidance_statement"),
    ("analyst_pressure", "analyst_pressure"),
    ("management_hedging", "management_hedging"),
    ("uncertainty", "uncertainty"),
    ("reassurance", "reassurance"),
    ("answer_shift", "answer_shift"),
    ("no_signal", "neutral/no_signal"),
    ("neutral", "neutral/no_signal"),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _safe_label_from_rule(row: dict[str, Any]) -> str:
    rule_id = str(row.get("rule_id", "")).strip().lower()
    for token, label in RULE_LABEL_HINTS:
        if token in rule_id:
            return label
    return str(row.get("suggested_label", "")).strip() or "needs_source_review"


def _missing_provenance(row: dict[str, Any]) -> bool:
    return any(not str(row.get(field, "")).startswith("sha256:") for field in PROVENANCE_FIELDS)


def _confidence(row: dict[str, Any], weak_label: str, existing_label: str, missing_provenance: bool) -> str:
    if missing_provenance:
        return "0.10"
    try:
        existing_confidence = float(row.get("suggested_confidence", "0.55"))
    except (TypeError, ValueError):
        existing_confidence = 0.55
    if weak_label != existing_label:
        value = min(existing_confidence, 0.45)
    else:
        value = min(max(existing_confidence, 0.25), 0.80)
    return f"{value:.2f}"


def _priority(weak_label: str, existing_label: str, missing_provenance: bool) -> str:
    if missing_provenance:
        return "needs_source_review"
    if weak_label != existing_label:
        return "highest"
    if weak_label in HIGH_PRIORITY_LABELS:
        return "high"
    if weak_label in MEDIUM_PRIORITY_LABELS:
        return "medium"
    if weak_label in LOW_PRIORITY_LABELS:
        return "low"
    return "medium"


def _reason_codes(
    *,
    row: dict[str, Any],
    registry_summary: dict[str, Any],
    weak_label: str,
    existing_label: str,
    missing_provenance: bool,
    calibration_ids: set[str],
) -> str:
    reasons = ["weak_model_assist", "metadata_only"]
    if not registry_summary.get("allowed_weak_review_assist_assets"):
        reasons.append("no_license_cleared_public_model")
    else:
        reasons.append("public_model_not_used_deterministic_default")
    if row.get("rule_id"):
        reasons.append("rule_id_hint")
    if missing_provenance:
        reasons.append("missing_provenance")
    if weak_label != existing_label:
        reasons.append("disagreement_with_existing")
    if str(row.get("candidate_id", "")) in calibration_ids:
        reasons.append("calibration_batch_reference")
    return ";".join(reasons)


def _assist_row(row: dict[str, Any], registry_summary: dict[str, Any], calibration_ids: set[str]) -> dict[str, str]:
    existing_label = str(row.get("suggested_label", "")).strip()
    missing_provenance = _missing_provenance(row)
    weak_label = "needs_source_review" if missing_provenance else _safe_label_from_rule(row)
    disagreement = weak_label != existing_label
    return {
        "candidate_id": str(row.get("candidate_id", "")),
        "case_id": str(row.get("case_id", "")),
        "ticker": str(row.get("ticker", "")),
        "fiscal_period": str(row.get("fiscal_period", "")),
        "existing_suggested_label": existing_label,
        "weak_model_suggested_label": weak_label,
        "weak_model_confidence": _confidence(row, weak_label, existing_label, missing_provenance),
        "assist_method": "metadata_rule_heuristic",
        "disagreement_flag": str(disagreement).lower(),
        "review_priority": _priority(weak_label, existing_label, missing_provenance),
        "reason_code": _reason_codes(
            row=row,
            registry_summary=registry_summary,
            weak_label=weak_label,
            existing_label=existing_label,
            missing_provenance=missing_provenance,
            calibration_ids=calibration_ids,
        ),
        "allowed_for_final_adjudication": "false",
        "gold_created": "false",
        "training_performed": "false",
        "raw_text_used": "false",
        "raw_text_returned": "false",
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ASSIST_FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    priority_counts = json.dumps(summary["priority_counts"], sort_keys=True)
    label_counts = json.dumps(summary["weak_label_counts"], sort_keys=True)
    lines = [
        "# First100 Weak Model Assist",
        "",
        "- Status: metadata-only weak_model_assist generated",
        f"- Rows: {summary['rows']}",
        f"- Assist method: {summary['assist_method']}",
        f"- Public/local model outputs used: {str(summary['public_model_outputs_used']).lower()}",
        f"- License-cleared weak-assist assets: {len(summary['license_cleared_weak_assist_assets'])}",
        f"- Downloads performed: {str(summary['downloads_performed']).lower()}",
        "- Raw text used: false",
        "- Raw text returned: false",
        "- Final adjudication automated: false",
        "- Gold labels created: 0",
        "- Training performed: false",
        f"- Disagreement flags: {summary['disagreement_flags']}",
        f"- Review priority counts: `{priority_counts}`",
        f"- Weak label counts: `{label_counts}`",
        "",
        "## Guardrail",
        "",
        "This file contains weak reviewer-support metadata only. It is not validator-ready adjudication, gold promotion, or training data.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_weak_model_assist(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES,
    calibration_path: Path = DEFAULT_CALIBRATION,
    registry_path: Path = DEFAULT_REGISTRY,
    out_csv: Path = DEFAULT_OUT,
    out_report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    registry_summary = validate_registry(registry_path)
    if not registry_summary["valid"]:
        raise SystemExit("public model assist registry is invalid; fail closed before weak-assist generation")
    candidates = read_jsonl(candidates_path)
    calibration_ids = {str(row.get("candidate_id", "")) for row in read_jsonl(calibration_path)}
    rows = [_assist_row(row, registry_summary, calibration_ids) for row in candidates]
    _write_csv(out_csv, rows)
    priority_counts = dict(sorted(Counter(row["review_priority"] for row in rows).items()))
    weak_label_counts = dict(sorted(Counter(row["weak_model_suggested_label"] for row in rows).items()))
    summary = {
        "rows": len(rows),
        "assist_method": "metadata_rule_heuristic",
        "public_model_outputs_used": False,
        "license_cleared_weak_assist_assets": registry_summary["allowed_weak_review_assist_assets"],
        "downloads_performed": registry_summary["download_performed"],
        "disagreement_flags": sum(1 for row in rows if row["disagreement_flag"] == "true"),
        "priority_counts": priority_counts,
        "weak_label_counts": weak_label_counts,
        "allowed_for_final_adjudication": False,
        "final_adjudication_automated": False,
        "gold_labels_created": 0,
        "training_performed": False,
        "raw_text_used": False,
        "raw_text_returned": False,
    }
    _write_report(out_report, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build metadata-only first100 weak model assist CSV.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_weak_model_assist(
        candidates_path=args.candidates,
        calibration_path=args.calibration,
        registry_path=args.registry,
        out_csv=args.out,
        out_report=args.report,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
