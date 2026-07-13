#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for import_path in (SRC, SCRIPTS):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from signal_engine.gold_review import audit_gold_labels

DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS = 100
DEFAULT_MIN_STRICT_VALID_ADJUDICATED_LABELS = DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS

STRICT_COUNT_BELOW_MINIMUM_BLOCKER = "strict_valid_gold_count_below_100"
CANONICAL_AUDIT_MISSING_BLOCKER = "canonical_gold_audit_missing"
CANONICAL_AUDIT_UNREADABLE_BLOCKER = "canonical_gold_audit_unreadable"


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def _is_adjudicated(row: dict[str, Any]) -> bool:
    adjudication_markers = (
        "review_status",
        "adjudication_status",
        "gold_status",
        "final_label_status",
    )
    return any(str(row.get(marker, "")).strip().lower() == "adjudicated" for marker in adjudication_markers)


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _policy_status(*, status: str, summary: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "fail_closed": True,
        "summary": summary,
        "evidence": evidence or {},
    }


def build_canonical_readiness_summary(
    *,
    gold_path: Path = ROOT / "data" / "gold" / "gold_labels.jsonl",
    minimum_strict_valid_gold_labels: int | None = None,
    min_strict_valid_adjudicated_labels: int | None = None,
) -> dict[str, Any]:
    if minimum_strict_valid_gold_labels is None:
        minimum_strict_valid_gold_labels = (
            min_strict_valid_adjudicated_labels
            if min_strict_valid_adjudicated_labels is not None
            else DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS
        )
    audit = audit_gold_labels(gold_path)
    audited = list(audit.get("audited") or [])
    strict_valid_rows = [item["row"] for item in audited if item.get("status") == "VALID"]
    strict_valid_adjudicated_rows = [row for row in strict_valid_rows if _is_adjudicated(row)]
    row_count = _safe_int(audit.get("row_count"))
    strict_valid_gold_count = len(strict_valid_rows)
    strict_valid_adjudicated_count = len(strict_valid_adjudicated_rows)
    status_counts = dict(audit.get("status_counts") or {})
    parse_error_count = _safe_int(audit.get("parse_error_count"))
    legacy_gold_count = max(row_count - strict_valid_gold_count, 0)
    blocked_status_counts = {
        status: count for status, count in status_counts.items() if str(status).startswith("BLOCKED")
    }
    non_valid_status_counts = {
        status: count for status, count in status_counts.items() if str(status) != "VALID"
    }
    blocked_gold_count = sum(int(count) for count in blocked_status_counts.values())
    missing_strict_labels = max(minimum_strict_valid_gold_labels - strict_valid_gold_count, 0)

    training_blockers: list[str] = []
    if not gold_path.exists():
        training_blockers.append(CANONICAL_AUDIT_MISSING_BLOCKER)
    elif parse_error_count:
        training_blockers.append(CANONICAL_AUDIT_UNREADABLE_BLOCKER)
    elif strict_valid_gold_count < minimum_strict_valid_gold_labels:
        training_blockers.append(STRICT_COUNT_BELOW_MINIMUM_BLOCKER)

    training_ready = not training_blockers
    training_status = "READY" if training_ready else "BLOCKED"
    status = "READY" if training_ready else "NOT_READY"
    training_gate_reason = (
        "strict_valid_gold_count_met_minimum" if training_ready else training_blockers[0]
    )
    repair_findings = {
        "legacy_gold_count": legacy_gold_count,
        "blocked_gold_count": blocked_gold_count,
        "repair_candidates": legacy_gold_count,
        "blocked_status_counts": dict(sorted(blocked_status_counts.items())),
        "non_valid_status_counts": dict(sorted(non_valid_status_counts.items())),
        "parse_error_count": parse_error_count,
        "repair_required": bool(legacy_gold_count or blocked_gold_count or parse_error_count),
        "training_gate_impact": "none",
    }

    provenance_status = "PASS" if not repair_findings["repair_required"] and row_count > 0 else "FAIL_CLOSED"
    claim_status = "PASS"
    artifact_status = "PASS"
    source_rights_status = "FAIL_CLOSED" if repair_findings["repair_required"] else "PASS"

    return {
        "schema_version": "canonical_readiness.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "canonical_gold_modified": False,
        "canonical_truth_source": {
            "validator": "signal_engine.gold_review.audit_gold_labels",
            "gold_path": _repo_relative(gold_path),
            "training_gate": "strict_valid_gold_count >= minimum_strict_valid_gold_labels",
        },
        "strict_valid_gold_count": strict_valid_gold_count,
        "legacy_gold_count": legacy_gold_count,
        "blocked_gold_count": blocked_gold_count,
        "minimum_strict_valid_gold_labels": minimum_strict_valid_gold_labels,
        "training_ready": training_ready,
        "training_status": training_status,
        "training_gate_reason": training_gate_reason,
        "training_blockers": training_blockers,
        "repair_findings": repair_findings,
        "repair_status_counts": {},
        "gold": {
            "source_path": _repo_relative(gold_path),
            "row_count": row_count,
            "parse_error_count": parse_error_count,
            "status_counts": status_counts,
            "strict_valid_gold_count": strict_valid_gold_count,
            "legacy_gold_count": legacy_gold_count,
            "blocked_gold_count": blocked_gold_count,
            "strict_valid_adjudicated_label_count": strict_valid_adjudicated_count,
            "legacy_gold_row_count": legacy_gold_count,
            "legacy_repair_candidate_count": legacy_gold_count,
            "training_ready_legacy_row_count": 0,
        },
        "training": {
            "status": training_status,
            "training_allowed": training_ready,
            "training_ready": training_ready,
            "minimum_strict_valid_gold_labels": minimum_strict_valid_gold_labels,
            "min_strict_valid_adjudicated_labels": minimum_strict_valid_gold_labels,
            "strict_valid_gold_count": strict_valid_gold_count,
            "strict_valid_adjudicated_label_count": strict_valid_adjudicated_count,
            "missing_strict_valid_gold_labels": missing_strict_labels,
            "missing_strict_valid_adjudicated_labels": missing_strict_labels,
            "training_gate_reason": training_gate_reason,
            "training_blockers": training_blockers,
            "blockers": training_blockers,
        },
        "policy": {
            "source_rights": _policy_status(
                status=source_rights_status,
                summary="Unknown or unrepaired legacy provenance is tracked separately from the strict training gate.",
                evidence=repair_findings,
            ),
            "provenance": _policy_status(
                status=provenance_status,
                summary="Only sha256-backed strict-valid rows can contribute to readiness.",
                evidence={
                    "strict_valid_gold_count": strict_valid_gold_count,
                    "minimum_strict_valid_gold_labels": minimum_strict_valid_gold_labels,
                    "row_count": row_count,
                },
            ),
            "artifact_policy": _policy_status(
                status=artifact_status,
                summary="No model weights, embeddings, raw transcript bodies, or provider outputs are produced.",
            ),
            "claim_safety": _policy_status(
                status=claim_status,
                summary="Alpha, trading performance, causal market impact, statistical significance, production ML, and production retrieval claims remain blocked.",
            ),
        },
        "audit_findings": {
            "status_counts": status_counts,
            "blocked_status_counts": dict(sorted(blocked_status_counts.items())),
            "non_valid_status_counts": dict(sorted(non_valid_status_counts.items())),
            "parse_error_count": parse_error_count,
        },
        "blockers": training_blockers,
        "next_actions": [
            "Repair legacy gold provenance through human-reviewed staging, not direct canonical edits.",
            "Adjudicate enough strict-valid labels to reach the 100-label training gate.",
            "Keep source rights, artifact policy, and claims validators in the Control Room status loop.",
        ],
    }


def write_readiness_outputs(summary: dict[str, Any], *, json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gold = summary["gold"]
    training = summary["training"]
    policy = summary["policy"]
    lines = [
        "# Canonical Readiness",
        "",
        "Operational truth is strict and fail-closed. Legacy gold rows are repair candidates, not training-ready labels.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Gold source: `{gold['source_path']}`",
        f"- Total canonical gold rows: `{gold['row_count']}`",
        f"- Strict-valid training gate: `{summary['strict_valid_gold_count']}` / `{summary['minimum_strict_valid_gold_labels']}`",
        f"- Strict-valid adjudicated labels (informational): `{training['strict_valid_adjudicated_label_count']}`",
        f"- Legacy repair candidate rows: `{gold['legacy_repair_candidate_count']}`",
        f"- Blocked gold rows (repair finding): `{summary['blocked_gold_count']}`",
        f"- Training: `{training['status']}`",
        f"- Training ready: `{summary['training_ready']}`",
        f"- Training gate reason: `{summary['training_gate_reason']}`",
        f"- Canonical gold modified: `{summary['canonical_gold_modified']}`",
        "",
        "No canonical gold rows were modified.",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(gold["status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(["", "## Policy Gates", ""])
    for name, payload in policy.items():
        lines.append(f"- `{name}`: `{payload['status']}` - {payload['summary']}")
    lines.extend(["", "## Training Blockers", ""])
    lines.extend(f"- `{blocker}`" for blocker in summary["training_blockers"] or ["none"])
    lines.extend(["", "## Repair Findings", ""])
    repair_findings = summary["repair_findings"]
    lines.extend(
        [
            f"- Legacy gold rows: `{repair_findings['legacy_gold_count']}`",
            f"- Blocked gold rows: `{repair_findings['blocked_gold_count']}`",
            f"- Repair candidates: `{repair_findings['repair_candidates']}`",
            f"- Repair required: `{repair_findings['repair_required']}`",
            "- Training gate impact: `none`",
        ]
    )
    lines.extend(["", "### Blocked Status Counts", ""])
    blocked_status_counts = repair_findings["blocked_status_counts"]
    lines.extend(f"- `{status}`: `{count}`" for status, count in blocked_status_counts.items() or [("none", 0)])
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in summary["next_actions"])
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build canonical readiness from strict gold-label audit state.")
    parser.add_argument("--gold", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--json-out", default="reports/readiness_canonical.json")
    parser.add_argument("--md-out", default="reports/readiness_canonical.md")
    parser.add_argument(
        "--minimum-strict-valid-gold-labels",
        "--min-strict-valid-adjudicated-labels",
        dest="minimum_strict_valid_gold_labels",
        type=int,
        default=DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS,
        help="Minimum strict-valid canonical gold labels required for training readiness.",
    )
    args = parser.parse_args(argv)

    summary = build_canonical_readiness_summary(
        gold_path=Path(args.gold),
        minimum_strict_valid_gold_labels=args.minimum_strict_valid_gold_labels,
    )
    write_readiness_outputs(summary, json_out=Path(args.json_out), md_out=Path(args.md_out))
    print(
        "Canonical readiness "
        f"{summary['status']}: {summary['strict_valid_gold_count']}/"
        f"{summary['minimum_strict_valid_gold_labels']} strict-valid gold rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
