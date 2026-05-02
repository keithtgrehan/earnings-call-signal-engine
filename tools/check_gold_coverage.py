#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import SIGNAL_LABELS, read_jsonl  # noqa: E402


def coverage(rows: list[dict[str, object]]) -> dict[str, object]:
    labels = Counter(str(row.get("signal_family") or row.get("label") or "") for row in rows)
    domains = Counter(str(row.get("domain") or row.get("case_id") or "unknown") for row in rows)
    return {
        "gold_labels": len(rows),
        "label_counts": {label: labels.get(label, 0) for label in sorted(SIGNAL_LABELS)},
        "missing_labels": sorted(label for label in SIGNAL_LABELS if labels.get(label, 0) == 0),
        "domain_or_case_counts": dict(domains),
    }


def write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Gold Label Status", "", f"- gold_labels: `{payload['gold_labels']}`", ""]
    lines.append("## Label Counts")
    lines.append("")
    for label, count in dict(payload["label_counts"]).items():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", f"- missing_labels: `{', '.join(payload['missing_labels']) or 'none'}`"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check gold-label coverage and write status docs.")
    parser.add_argument("--gold", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "docs" / "labeling" / "gold_label_status.md"))
    args = parser.parse_args(argv)
    rows = read_jsonl(Path(args.gold))
    payload = coverage(rows)
    write_report(Path(args.out), payload)
    print(payload)
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
