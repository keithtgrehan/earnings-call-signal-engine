#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluation_quality import (  # noqa: E402
    EVIDENCE_OBJECTS_PATH,
    GOLD_PATH,
    deterministic_predictions,
    read_jsonl,
    row_text,
    write_jsonl,
)


def build_objects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predictions = deterministic_predictions(rows)
    by_id = {str(row["id"]): row for row in predictions}
    output: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("id") or row.get("candidate_id") or "")
        prediction = by_id.get(row_id)
        if prediction is None or not row_text(row):
            continue
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        output.append(
            {
                "case_id": str(row.get("case_id") or ""),
                "speaker": str(row.get("speaker") or row.get("speaker_role") or meta.get("speaker") or "unknown"),
                "section": str(row.get("section") or meta.get("section") or "unknown"),
                "text": row_text(row),
                "gold_label": prediction["gold_label"],
                "deterministic_label": prediction["deterministic_label"],
                "deterministic_score": prediction["deterministic_score"],
                "source_group": prediction["source_group"],
                "provenance_quality": prediction["provenance_quality"],
                "requires_manual_review": prediction["requires_manual_review"],
            }
        )
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build canonical evidence objects for benchmark-only retrieval experiments.")
    parser.add_argument("--gold", default=str(GOLD_PATH))
    parser.add_argument("--out", default=str(EVIDENCE_OBJECTS_PATH))
    args = parser.parse_args(argv)
    objects = build_objects(read_jsonl(Path(args.gold)))
    write_jsonl(Path(args.out), objects)
    print(json.dumps({"status": "ok", "objects": len(objects), "out": args.out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
