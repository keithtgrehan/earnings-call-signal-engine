#!/usr/bin/env python
from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "nlp_assets"
DOC_DIR = ROOT / "docs" / "nlp_assets"


def main() -> int:
    entries = json.loads((DATA_DIR / "asset_registry.json").read_text(encoding="utf-8"))
    status_counts = collections.Counter(entry["download_status"] for entry in entries)
    priority_counts = collections.Counter(entry["priority"] for entry in entries)
    category_counts = collections.Counter(entry["category"] for entry in entries)
    downloaded = [entry for entry in entries if entry["download_status"] == "downloaded"]
    manual = [entry for entry in entries if entry["download_status"] in {"manual_required", "gated"}]

    summary = {
        "asset_count": len(entries),
        "status_counts": dict(status_counts),
        "priority_counts": dict(priority_counts),
        "category_counts": dict(category_counts),
        "downloaded_assets": [entry["id"] for entry in downloaded],
        "manual_or_gated_assets": [entry["id"] for entry in manual],
    }
    (DATA_DIR / "asset_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (DOC_DIR / "download_status.md").write_text(
        "# NLP Asset Download Status\n\n"
        "Downloaded means the safe tooling cached a small public metadata/reference artifact. It does not imply raw training data availability unless explicitly stated.\n\n"
        "## Status Counts\n\n"
        + "\n".join(f"- `{status}`: {count}" for status, count in sorted(status_counts.items()))
        + "\n\n## Downloaded Safe Cache Artifacts\n\n"
        + ("\n".join(f"- {entry['name']}: `{entry['local_path']}`" for entry in downloaded) or "- None")
        + "\n\n## Manual Or Gated Assets\n\n"
        + "\n".join(f"- {entry['name']} (`{entry['download_status']}`): {entry['license']}" for entry in manual)
        + "\n",
        encoding="utf-8",
    )
    print(f"Summarized {len(entries)} NLP assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
