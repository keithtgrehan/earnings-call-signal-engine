#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from resource_registry_common import normalize_resource_rows, read_structured, validate_resource_rows

ROOT = Path(__file__).resolve().parents[1]


def build_dashboard(registry_path: Path) -> str:
    rows = normalize_resource_rows(read_structured(registry_path))
    errors = validate_resource_rows(rows)
    by_tier = Counter(str(row.get("rights_tier", "missing")) for row in rows)
    by_type = Counter(str(row.get("source_type", "missing")) for row in rows)
    blocked = [row for row in rows if row.get("allowed_storage") == "blocked" or row.get("blocked_reason")]
    raw_allowed = [row for row in rows if row.get("raw_body_allowed") is True]

    lines = [
        "# Corpus Resource Status Dashboard",
        "",
        "Generated from the resource registry. This dashboard is metadata-only and performs no downloads.",
        "",
        f"- registry: `{registry_path}`",
        f"- resources: `{len(rows)}`",
        f"- validation_status: `{'valid' if not errors else 'invalid'}`",
        f"- validation_errors: `{len(errors)}`",
        f"- raw_body_allowed_records: `{len(raw_allowed)}`",
        f"- blocked_records: `{len(blocked)}`",
        "",
        "## Rights Tier Counts",
        "",
    ]
    for key, count in sorted(by_tier.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Source Type Counts", ""])
    for key, count in sorted(by_type.items()):
        lines.append(f"- `{key}`: `{count}`")
    if errors:
        lines.extend(["", "## Validation Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    lines.extend(["", "## Blocked Cases", ""])
    if blocked:
        for row in blocked:
            lines.append(f"- `{row.get('source_id')}`: {row.get('blocked_reason') or 'blocked by storage policy'}")
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a metadata-only resource/corpus dashboard.")
    parser.add_argument("--registry", default=str(ROOT / "configs" / "resource_registry.example.yml"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "corpus_resource_status_dashboard.md"))
    args = parser.parse_args(argv)

    text = build_dashboard(Path(args.registry))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote dashboard to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
