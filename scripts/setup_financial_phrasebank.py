#!/usr/bin/env python3
"""Create a local-only Financial PhraseBank intake manifest.

This script does not download data. Place a license-reviewed local export in the
created folder, then run scripts/import_financial_phrasebank.py.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DIR = ROOT / "data" / "external" / "financial_phrasebank"


def main() -> int:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": "Financial PhraseBank",
        "source": "https://www.researchgate.net/publication/251231364_FinancialPhraseBank-v10",
        "license_note": "Manual download and license review required before local use.",
        "local_path": str(LOCAL_DIR),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "next_step": "Place CSV/TSV/TXT export here, then run scripts/import_financial_phrasebank.py.",
    }
    path = LOCAL_DIR / "setup_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote local-only setup manifest: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
