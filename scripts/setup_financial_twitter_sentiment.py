#!/usr/bin/env python3
"""Create a local-only Financial Twitter Sentiment intake manifest.

This script does not download data. Use only data that Keith has permission to
store locally, then add a loader once the exact source format is known.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DIR = ROOT / "data" / "external" / "financial_twitter_sentiment"


def main() -> int:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": "Financial Twitter Sentiment candidate",
        "source": "Manual source required; do not scrape or bypass platform terms.",
        "license_note": "Manual license and privacy review required before local use.",
        "local_path": str(LOCAL_DIR),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "next_step": "Place a permitted export here and document its schema before adding a loader.",
    }
    path = LOCAL_DIR / "setup_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote local-only setup manifest: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
