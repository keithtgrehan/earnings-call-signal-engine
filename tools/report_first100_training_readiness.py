#!/usr/bin/env python3
"""Report first100 review and training readiness without training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
DEFAULT_PROMOTION_JSON = ROOT / "reports" / "review" / "first100_promotion_manifest_validation.json"
PACKET_DIR = ROOT / "data" / "review" / "packets"
REPORT_PATH = ROOT / "reports" / "review" / "first100_training_readiness.md"
JSON_REPORT_PATH = ROOT / "reports" / "review" / "first100_training_readiness.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _training_rights_explicit() -> bool:
    license_dir = ROOT / "data" / "provider_license_configs"
    if not license_dir.exists():
        return False
    for path in license_dir.glob("*.yml"):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "training_allowed: true" in text and "explicit_training_rights_ref:" in text and "pending" not in text:
            return True
    return False


def report(
    candidates_path: Path = DEFAULT_CANDIDATES,
    promotion_json_path: Path = DEFAULT_PROMOTION_JSON,
    out_path: Path = REPORT_PATH,
    json_out_path: Path = JSON_REPORT_PATH,
) -> dict[str, Any]:
    candidates = read_jsonl(candidates_path)
    packets = list(PACKET_DIR.glob("first100_batch_*.md"))
    promotion = read_json(promotion_json_path)
    valid_adjudicated_labels = promotion.get("rows", 0) if promotion.get("valid") else 0
    provenance_complete = bool(candidates) and all(
        row.get("source_sha256") and row.get("normalized_transcript_hash") and row.get("provenance_hash") for row in candidates
    )
    training_rights = _training_rights_explicit()
    if promotion.get("valid") and valid_adjudicated_labels >= 100 and provenance_complete and training_rights:
        state = "TRAINING_READY_STAGED"
    elif promotion.get("valid"):
        state = "PROMOTION_READY"
    elif len(candidates) >= 100 and len(packets) >= 5:
        state = "REVIEW_READY"
    else:
        state = "NOT_READY"
    canonical_state = "TRAINING_READY_CANONICAL" if state == "TRAINING_READY_STAGED" and False else state
    blockers = []
    if len(candidates) < 100:
        blockers.append(f"pending candidate count below review threshold: {len(candidates)}/100")
    if len(packets) < 5:
        blockers.append(f"review packet count below expected 5: {len(packets)}")
    if valid_adjudicated_labels < 100:
        blockers.append(f"valid adjudicated labels below training gate: {valid_adjudicated_labels}/100")
    if not training_rights:
        blockers.append("explicit training rights are not configured")
    if not promotion.get("valid"):
        blockers.append("promotion manifest is not valid or not present")
    summary = {
        "state": state,
        "canonical_state": canonical_state,
        "pending_candidates": len(candidates),
        "packet_count": len(packets),
        "valid_adjudicated_labels": valid_adjudicated_labels,
        "provenance_complete": provenance_complete,
        "training_rights_explicit": training_rights,
        "training_performed": False,
        "gold_labels_created": 0,
        "blockers": blockers,
    }
    write_reports(summary, out_path, json_out_path)
    return summary


def write_reports(summary: dict[str, Any], out_path: Path, json_out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Training Readiness",
        "",
        f"- State: {summary['state']}",
        f"- Canonical state: {summary['canonical_state']}",
        f"- Pending candidates: {summary['pending_candidates']}",
        f"- Review packets: {summary['packet_count']}",
        f"- Valid adjudicated labels: {summary['valid_adjudicated_labels']}",
        f"- Provenance complete: {str(summary['provenance_complete']).lower()}",
        f"- Explicit training rights: {str(summary['training_rights_explicit']).lower()}",
        "- Training performed: false",
        "- Gold labels created: 0",
        "",
        "## Blockers",
        "",
    ]
    blockers = summary.get("blockers") or []
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    json_out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report first100 training readiness without training.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--promotion-json", type=Path, default=DEFAULT_PROMOTION_JSON)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--json-out", type=Path, default=JSON_REPORT_PATH)
    args = parser.parse_args(argv)
    print(json.dumps(report(args.candidates, args.promotion_json, args.out, args.json_out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
