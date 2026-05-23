#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from agent5_rights_gated_builders import build_permitted_ingest_queue, write_markdown, write_yaml


def _load_candidates(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = payload.get("candidates") if isinstance(payload, dict) else payload
    return rows if isinstance(rows, list) else []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build permitted ingest queue from explicitly allowed candidates; no ingest is performed.")
    parser.add_argument("--candidates", default="data/corpus/official_ir_candidate_map.yml")
    parser.add_argument("--out", default="data/corpus/permitted_ingest_queue.yml")
    parser.add_argument("--report", default="reports/agent5/permitted_ingest_queue.md")
    args = parser.parse_args(argv)
    rows = build_permitted_ingest_queue(_load_candidates(Path(args.candidates)))
    write_yaml(Path(args.out), "queue", rows)
    write_markdown(Path(args.report), "Permitted Ingest Queue", [f"- Rows: `{len(rows)}`", "- Empty is valid when no candidate has explicit raw-use permission.", "- No raw ingest performed."])
    print(f"Permitted ingest queue written: {len(rows)} row(s); no raw ingest performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
