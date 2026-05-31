#!/usr/bin/env python3
"""Build a metadata-only reviewer helper packet for first100 adjudication."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "review" / "staging" / "first100_signal_candidates.jsonl"
ADJUDICATION_DRAFT = ROOT / "data" / "review" / "staging" / "first100_adjudication_draft.jsonl"
REPORT_MD = ROOT / "reports" / "review" / "first100_reviewer_packet.md"
REPORT_JSON = ROOT / "reports" / "review" / "first100_reviewer_packet.json"
GUIDE_PATH = ROOT / "docs" / "review" / "first100_manual_adjudication_guide.md"
ROW_TEMPLATE_PATH = ROOT / "docs" / "review" / "first100_adjudication_row_template.json"

REVIEWER_FIELDS = [
    "candidate_id",
    "reviewer",
    "adjudicated_label",
    "rationale",
    "rejection_reason",
    "evidence/provenance references",
    "promotion_decision=not_requested",
    "training flags=false",
]

VALIDATION_COMMANDS = [
    "python3 tools/validate_first100_adjudication_file.py data/review/staging/first100_adjudication_draft.jsonl",
    "python3 tools/validate_first100_promotion_manifest.py --manifest data/review/staging/first100_promotion_manifest.jsonl",
    "python3 tools/build_review_readiness_dashboard.py",
]


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _repo_display(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (OSError, ValueError):
        return str(path)


def _require_reports_review(root: Path, path: Path) -> None:
    reports_review = (root / "reports" / "review").resolve()
    resolved = path.resolve()
    if resolved != reports_review and reports_review not in resolved.parents:
        raise ValueError(f"reviewer packet outputs must stay under reports/review: {path}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sha256_or_missing(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_ids(rows: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for row in rows:
        candidate_id = str(row.get("candidate_id", "")).strip()
        if candidate_id:
            ids.append(candidate_id)
    return ids


def build_reviewer_packet(
    *,
    root: Path = ROOT,
    candidates_path: Path = CANDIDATES,
    draft_path: Path = ADJUDICATION_DRAFT,
    md_out: Path = REPORT_MD,
    json_out: Path = REPORT_JSON,
) -> dict[str, Any]:
    root = root.resolve()
    candidates_path = _resolve(root, candidates_path)
    draft_path = _resolve(root, draft_path)
    md_out = _resolve(root, md_out)
    json_out = _resolve(root, json_out)
    _require_reports_review(root, md_out)
    _require_reports_review(root, json_out)

    draft_hash_before = _sha256_or_missing(draft_path)
    rows = _read_jsonl(candidates_path)
    candidate_ids = _candidate_ids(rows)
    blockers: list[str] = []
    if not candidates_path.exists():
        blockers.append("candidate metadata missing")
    elif not candidate_ids:
        blockers.append("candidate metadata empty")
    if not draft_path.exists():
        blockers.append("adjudication draft missing")
    draft_hash_after = _sha256_or_missing(draft_path)

    summary = {
        "status": "REVIEW_PACKET_READY" if candidate_ids and not blockers else "NOT_READY",
        "candidate_count": len(candidate_ids),
        "candidate_ids": candidate_ids,
        "candidate_metadata_path": _repo_display(root, candidates_path),
        "adjudication_draft_path": _repo_display(root, draft_path),
        "manual_guide": _repo_display(root, GUIDE_PATH),
        "row_template": _repo_display(root, ROW_TEMPLATE_PATH),
        "reviewer_fields_to_fill": REVIEWER_FIELDS,
        "validation_commands": VALIDATION_COMMANDS,
        "checklist": [
            "Open the manual guide before editing.",
            "Copy only metadata identifiers and hashes.",
            "Leave promotion and training blocked.",
            "Do not paste transcript, audio, ASR, or chunk text.",
            "Run validation after manual edits.",
        ],
        "blockers": blockers,
        "staging_draft_modified": draft_hash_before != draft_hash_after,
        "gold_labels_created": 0,
        "promotion_rows_created": 0,
        "training_data_created": False,
        "promotion_ready": False,
        "training_ready": False,
        "raw_text_included": False,
    }
    _write_reports(root, summary, md_out, json_out)
    return summary


def _write_reports(root: Path, summary: dict[str, Any], md_out: Path, json_out: Path) -> None:
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First100 Reviewer Packet",
        "",
        "- Purpose: help humans fill adjudication rows manually.",
        f"- Status: {summary['status']}",
        f"- Candidate count: {summary['candidate_count']}",
        "- Review-only output: true",
        "- Gold labels created: 0",
        "- Promotion ready: false",
        "- Training ready: false",
        "- Raw evidence text included: false",
        "",
        "## References",
        "",
        f"- Manual guide: `{summary['manual_guide']}`",
        f"- Documentation row template: `{summary['row_template']}`",
        f"- Adjudication draft: `{summary['adjudication_draft_path']}`",
        "",
        "## Candidate IDs",
        "",
    ]
    if summary["candidate_ids"]:
        lines.extend(f"- `{candidate_id}`" for candidate_id in summary["candidate_ids"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Empty Fields Reviewers Fill",
            "",
        ]
    )
    lines.extend(f"- `{field}`" for field in summary["reviewer_fields_to_fill"])
    lines.extend(
        [
            "",
            "## Checklist",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["checklist"])
    lines.extend(
        [
            "",
            "## Validation Commands",
            "",
            "```bash",
            *summary["validation_commands"],
            "```",
            "",
            "## Blockers",
            "",
        ]
    )
    blockers = summary.get("blockers") or []
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a reviewer-only first100 adjudication helper packet.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--candidates", type=Path, default=CANDIDATES)
    parser.add_argument("--draft", type=Path, default=ADJUDICATION_DRAFT)
    parser.add_argument("--out", type=Path, default=REPORT_MD)
    parser.add_argument("--json-out", type=Path, default=REPORT_JSON)
    args = parser.parse_args(argv)
    summary = build_reviewer_packet(
        root=args.root,
        candidates_path=args.candidates,
        draft_path=args.draft,
        md_out=args.out,
        json_out=args.json_out,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "REVIEW_PACKET_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
