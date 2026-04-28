#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("cases", "datasets"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError("Manifest must be CSV, JSON list, or JSON object with a cases list.")


def find_case(rows: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get("case_id", "")).strip() == case_id:
            return row
    raise ValueError(f"case_id not found in manifest: {case_id}")


def render_readme(case: dict[str, Any]) -> str:
    case_id = str(case.get("case_id", ""))
    source_url = str(case.get("source_url", ""))
    transcript_path = str(case.get("transcript_path", ""))
    return "\n".join(
        [
            f"# Manual Corpus Case: {case_id}",
            "",
            "This folder is a manual intake scaffold only. It does not contain downloaded transcript text by default.",
            "",
            "## Source Metadata",
            "",
            f"- ticker: `{case.get('ticker', '')}`",
            f"- company_name: `{case.get('company_name', case.get('company', ''))}`",
            f"- fiscal_period: `{case.get('fiscal_period', '')}`",
            f"- call_date: `{case.get('call_date', '')}`",
            f"- source_category: `{case.get('source_category', '')}`",
            f"- source_url: `{source_url}`",
            f"- intended transcript_path: `{transcript_path}`",
            "",
            "## Manual Checklist",
            "",
            "- Confirm source rights and access manually.",
            "- Do not scrape transcript vendors or paid sources.",
            "- Save only permitted transcript text.",
            "- Record source URL, source category, and any licensing notes.",
            "- Keep raw transcript text out of git unless explicitly approved.",
            "- Add manual labels only after source and section quality are reviewed.",
            "- Promote the case only after provenance, speaker roles, and evidence spans are checked.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create an empty manual corpus case folder from a manifest row.")
    parser.add_argument("--manifest", required=True, help="Manifest CSV or JSON path.")
    parser.add_argument("--case-id", required=True, help="Case ID to scaffold.")
    parser.add_argument("--out-root", required=True, help="Output root for case folders.")
    parser.add_argument("--force", action="store_true", help="Overwrite README/checklist if it already exists.")
    args = parser.parse_args(argv)

    case = find_case(load_manifest(Path(args.manifest)), args.case_id)
    case_dir = Path(args.out_root) / args.case_id
    for child in ("raw", "processed", "labels", "reports"):
        (case_dir / child).mkdir(parents=True, exist_ok=True)

    readme = case_dir / "README.md"
    if readme.exists() and not args.force:
        print(f"Case folder exists and README is present: {readme}")
        return 1
    readme.write_text(render_readme(case), encoding="utf-8")
    print(f"Manual corpus case scaffold written: {case_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
