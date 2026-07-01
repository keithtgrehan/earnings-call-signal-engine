#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

BATCH_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "fiscal_period",
    "local_path",
    "source_url",
    "source_type",
    "rights_tier",
    "operator",
    "eval_allowed",
    "training_allowed",
    "commit_allowed",
    "notes",
]


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _infer_ticker(case_id: str, path: str) -> str:
    candidates = [case_id, Path(path).stem]
    for value in candidates:
        match = re.search(r"\b([A-Za-z]{1,6})[_ -]?(20\d{2})", value)
        if match:
            return match.group(1).upper()
    prefix = re.split(r"[_\-\s]", Path(path).stem, maxsplit=1)[0]
    return prefix.upper() if prefix.isalpha() and len(prefix) <= 6 else ""


def _infer_period(case_id: str, path: str) -> str:
    text = f"{case_id} {Path(path).stem}".lower()
    match = re.search(r"(20\d{2})[_ -]?(q[1-4])", text)
    if not match:
        return ""
    return f"{match.group(1)}_{match.group(2).upper()}"


def _looks_like_whole_transcript(path: str) -> bool:
    path_obj = Path(path)
    stem = path_obj.stem.lower()
    parts = {part.lower() for part in path_obj.parts}
    if "transcript" in stem:
        return True
    if parts.intersection({"analysis", "labels", "outputs", "sections", "demo"}):
        return False
    return bool(re.search(r"[A-Za-z]{1,6}[_ -]?20\d{2}[_ -]?Q[1-4]", path_obj.stem, flags=re.IGNORECASE))


def build_batch_rows(discovery_rows: Iterable[dict[str, object]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in discovery_rows:
        if row.get("status") != "candidate_metadata_only":
            continue
        path = str(row.get("path_ref", "")).strip()
        if not path:
            continue
        if not _looks_like_whole_transcript(path):
            continue
        case_id = str(row.get("candidate_case_id") or Path(path).stem).strip()
        rows.append(
            {
                "case_id": case_id,
                "ticker": _infer_ticker(case_id, path),
                "company_name": "",
                "fiscal_period": _infer_period(case_id, path),
                "local_path": path,
                "source_url": "",
                "source_type": "manual_local",
                "rights_tier": "unknown",
                "operator": "",
                "eval_allowed": "false",
                "training_allowed": "false",
                "commit_allowed": "false",
                "notes": "Human fill required: source_url, rights_tier, and eval_allowed must be reviewed before registration.",
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BATCH_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_report(path: Path, rows: list[dict[str, str]], discovery_rows: list[dict[str, object]]) -> None:
    statuses = Counter(str(row.get("status", "unknown")) for row in discovery_rows)
    lines = [
        "# Manual-Local Batch Candidate Summary",
        "",
        f"- Discovery rows: `{len(discovery_rows)}`",
        f"- Batch candidate rows: `{len(rows)}`",
        f"- Blocked discovery rows excluded: `{sum(count for status, count in statuses.items() if status.startswith('blocked'))}`",
        "- Rights tier default: `unknown`",
        "- Commit/training/eval defaults: `false`",
        "- Registration automatic: `false`",
        "",
        "Human action: fill source URL and rights context before running registration.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a human-fill manual-local transcript batch CSV from discovery metadata.")
    parser.add_argument("--input", default="data/review/staging/manual_local_discovery_candidates.jsonl")
    parser.add_argument("--out", default="data/review/staging/manual_local_batch_candidate.csv")
    parser.add_argument("--report", default="reports/manual_local_batch_candidate_summary.md")
    args = parser.parse_args(argv)
    discovery_rows = _load_jsonl(Path(args.input))
    rows = build_batch_rows(discovery_rows)
    _write_csv(Path(args.out), rows)
    _write_report(Path(args.report), rows, discovery_rows)
    print(f"Manual-local batch candidate written: {len(rows)} row(s), no registration performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
