from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.corpus import validate_manifest_csv


def main() -> None:
    manifest_path = Path("data/corpus/manifests/pilot_corpus_manifest.csv")
    summary = validate_manifest_csv(manifest_path)
    print(json.dumps(summary, indent=2))
    if summary["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
