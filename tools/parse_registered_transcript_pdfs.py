#!/usr/bin/env python3
"""Re-parse downloaded first30 PDF/HTML/TXT transcript files from the Desktop audit log."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.download_first30_transcripts import download_first30_transcripts  # noqa: E402
from tools.first30_transcript_common import (  # noqa: E402
    DESKTOP_WORKSPACE,
    FIRST30_INGESTION_MANIFEST_PATH,
    MANUAL_TRANSCRIPT_REGISTRY_PATH,
    PARSED_TRANSCRIPT_REGISTRY_PATH,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse registered first30 transcript PDFs. The downloader already performs parsing; "
            "this command re-runs the same idempotent Desktop-only path for consistency."
        )
    )
    parser.add_argument("--manifest", type=Path, default=FIRST30_INGESTION_MANIFEST_PATH)
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    parser.add_argument("--registry", type=Path, default=MANUAL_TRANSCRIPT_REGISTRY_PATH)
    parser.add_argument("--parsed-registry", type=Path, default=PARSED_TRANSCRIPT_REGISTRY_PATH)
    args = parser.parse_args(argv)
    summary = download_first30_transcripts(
        manifest_path=args.manifest,
        workspace=args.workspace,
        registry_path=args.registry,
        parsed_registry_path=args.parsed_registry,
    )
    summary["mode"] = "idempotent_parse_refresh"
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
