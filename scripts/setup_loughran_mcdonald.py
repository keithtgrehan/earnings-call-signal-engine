#!/usr/bin/env python3
"""Create a local-only Loughran-McDonald intake manifest.

This script does not download data. Place the official, license-reviewed master
dictionary CSV in the created folder, then run scripts/import_loughran_mcdonald.py.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DIR = ROOT / "data" / "external" / "loughran_mcdonald"


def main() -> int:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": "Loughran-McDonald Master Dictionary",
        "source": "https://sraf.nd.edu/loughranmcdonald-master-dictionary/",
        "license_note": "Manual download and license review required before local use.",
        "local_path": str(LOCAL_DIR),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "next_step": "Place Loughran-McDonald_MasterDictionary_*.csv here, then run scripts/import_loughran_mcdonald.py.",
    }
    path = LOCAL_DIR / "setup_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote local-only setup manifest: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
