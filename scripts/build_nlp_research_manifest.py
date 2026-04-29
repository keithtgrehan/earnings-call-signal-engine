#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.research_sources import build_nlp_manifest_payload, render_nlp_manifest_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an offline-safe transcript-first NLP research manifest."
    )
    parser.add_argument(
        "--json-out",
        default=str(ROOT / "data" / "nlp_research" / "research_manifest.json"),
        help="Path to the JSON manifest output.",
    )
    parser.add_argument(
        "--markdown-out",
        default=str(ROOT / "docs" / "nlp-research-manifest.md"),
        help="Path to the Markdown manifest output.",
    )
    args = parser.parse_args(argv)

    payload = build_nlp_manifest_payload()
    json_out = Path(args.json_out)
    markdown_out = Path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_out.write_text(render_nlp_manifest_markdown(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "entry_count": payload["entry_count"],
                "json_out": str(json_out),
                "markdown_out": str(markdown_out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
