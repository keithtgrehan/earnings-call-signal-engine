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

from build_canonical_readiness import build_canonical_readiness_summary
from validate_training_plan import build_summary as build_training_plan_summary


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _canonical_readiness(path: Path, *, gold_path: Path) -> tuple[dict[str, Any], str, bool]:
    if path.exists():
        return _load_json(path), str(path), True
    return (
        build_canonical_readiness_summary(gold_path=gold_path),
        "computed:scripts/build_canonical_readiness.py",
        True,
    )


def _training_plan_context(path: Path) -> dict[str, Any]:
    try:
        summary = build_training_plan_summary(path)
    except Exception as exc:
        return {
            "path": str(path),
            "status": "invalid",
            "readiness_blockers": [str(exc)],
            "authority": "context_only",
        }
    return {
        "path": str(path),
        "status": summary.get("status", "unknown"),
        "readiness_blockers": list(summary.get("readiness_blockers") or []),
        "authority": "context_only",
    }


def build_training_readiness_report(
    *,
    canonical_readiness_path: Path,
    training_plan_path: Path,
    gold_path: Path,
) -> dict[str, Any]:
    canonical, authoritative_source, canonical_authoritative = _canonical_readiness(
        canonical_readiness_path,
        gold_path=gold_path,
    )
    training_ready = bool(canonical.get("training_ready"))
    if canonical.get("status") == "NOT_READY" or canonical.get("training_status") == "BLOCKED":
        training_ready = False
    training_status = "READY" if training_ready else "BLOCKED"
    status = "READY" if training_ready else "NOT_READY"
    return {
        "schema_version": "training_readiness_report.v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "training_status": training_status,
        "training_ready": training_ready,
        "training_attempted": False,
        "authoritative_source": authoritative_source,
        "canonical_authoritative": canonical_authoritative,
        "strict_valid_gold_count": int(canonical.get("strict_valid_gold_count") or 0),
        "minimum_strict_valid_gold_labels": int(canonical.get("minimum_strict_valid_gold_labels") or 100),
        "training_gate_reason": str(canonical.get("training_gate_reason") or "unknown"),
        "training_blockers": list(canonical.get("training_blockers") or canonical.get("blockers") or []),
        "repair_findings": dict(canonical.get("repair_findings") or {}),
        "canonical_readiness_status": str(canonical.get("status", "NOT_READY")),
        "canonical_readiness_path": str(canonical_readiness_path),
        "training_plan_context": _training_plan_context(training_plan_path),
        "notes": [
            "Canonical readiness is the training-readiness authority.",
            "Training plan validation is context only in this report.",
            "No model training, exports, embeddings, downloads, or provider calls were run.",
        ],
    }


def write_training_readiness_report(summary: dict[str, Any], *, json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Training Readiness",
        "",
        "No model training was run. This report derives readiness from canonical readiness only.",
        "",
        "## Canonical readiness authority",
        "",
        f"- Authoritative source: `{summary['authoritative_source']}`",
        f"- Status: `{summary['status']}`",
        f"- Training: `{summary['training_status']}`",
        f"- Training ready: `{summary['training_ready']}`",
        f"- Strict-valid gold rows: `{summary['strict_valid_gold_count']}` / `{summary['minimum_strict_valid_gold_labels']}`",
        f"- Training gate reason: `{summary['training_gate_reason']}`",
        f"- Training attempted: `{summary['training_attempted']}`",
        "",
        "## Training Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in summary["training_blockers"] or ["none"])
    repair_findings = summary["repair_findings"]
    lines.extend(
        [
            "",
            "## Repair Findings",
            "",
            f"- Legacy gold rows: `{repair_findings.get('legacy_gold_count', 0)}`",
            f"- Blocked gold rows: `{repair_findings.get('blocked_gold_count', 0)}`",
            f"- Repair candidates: `{repair_findings.get('repair_candidates', 0)}`",
            f"- Repair required: `{repair_findings.get('repair_required', False)}`",
            "",
            "## Training Plan Context",
            "",
            f"- Path: `{summary['training_plan_context']['path']}`",
            f"- Status: `{summary['training_plan_context']['status']}`",
            "- Authority: `context_only`",
        ]
    )
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report training readiness without training.")
    parser.add_argument("--path", default="configs/training_plan.example.yml")
    parser.add_argument("--gold", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--canonical-readiness", default="reports/readiness_canonical.json")
    parser.add_argument("--json-out", default="reports/training_readiness.json")
    parser.add_argument("--md-out", default="reports/training_readiness.md")
    args = parser.parse_args(argv)

    summary = build_training_readiness_report(
        canonical_readiness_path=Path(args.canonical_readiness),
        training_plan_path=Path(args.path),
        gold_path=Path(args.gold),
    )
    write_training_readiness_report(summary, json_out=Path(args.json_out), md_out=Path(args.md_out))
    print(f"Training readiness report written with canonical status {summary['status']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
