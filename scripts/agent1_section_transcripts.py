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

from signal_engine.agent1_extraction import section_transcript_text
from agent1_validate_manual_local_sources import load_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Section registered manual-local transcripts without committing raw text.")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--out", default="reports/agent1/sectioned_transcripts.jsonl")
    args = parser.parse_args(argv)
    rows = [row for row in load_registry(Path(args.registry)) if row.get("media_type") == "transcript"]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            source_path = Path(str(row.get("source_path_ref", "")))
            if not source_path.exists():
                continue
            sectioned = section_transcript_text(source_path.read_text(encoding="utf-8"))
            safe_turns = [{key: value for key, value in turn.items() if key != "text"} for turn in sectioned["speaker_turns"]]
            handle.write(
                json.dumps(
                    {
                        "case_id": row["case_id"],
                        "source_file": row["source_path_ref"],
                        "source_sha256": row["source_sha256"],
                        "sections": sectioned["sections"],
                        "speaker_turns": safe_turns,
                        "quality_flags": sectioned.get("quality_flags", {}),
                        "sectioning_confidence": sectioned.get("sectioning_confidence", "unknown"),
                        "raw_text_committed": False,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    print(f"Agent 1 sectioning complete: {len(rows)} registered transcript row(s), raw text not committed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
