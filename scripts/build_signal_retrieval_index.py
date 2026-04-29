#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation_backbone import write_json
from signal_engine.signal_baseline import HUMAN_REVIEWED_LABELS_RELATIVE_PATH, load_supervised_examples


def _sentence_transformers_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a lightweight retrieval index over labeled signal examples.")
    parser.add_argument("--input-path", default=str(ROOT / HUMAN_REVIEWED_LABELS_RELATIVE_PATH))
    parser.add_argument(
        "--index-out",
        default=str(ROOT / "data" / "nlp_research" / "signal_retrieval_index.json"),
    )
    parser.add_argument(
        "--status-out",
        default=str(ROOT / "data" / "nlp_research" / "signal_retrieval_status.json"),
    )
    args = parser.parse_args(argv)

    rows = load_supervised_examples(Path(args.input_path))
    index_payload = {
        "status": "ok",
        "generated_at": datetime.now(UTC).isoformat(),
        "backend": "tfidf_cosine",
        "optional_sentence_transformers_available": _sentence_transformers_available(),
        "example_count": len(rows),
        "examples": [
            {
                "id": row["id"],
                "text": row["text"],
                "signal_family": row["signal_family"],
                "evidence_terms": row.get("evidence_terms", []),
                "domain": row.get("domain"),
                "source_file": row.get("source_file"),
            }
            for row in rows
        ],
        "build_parameters": {
            "ngram_range": [1, 2],
            "lowercase": True,
            "notes": "The stored index is lightweight metadata; the TF-IDF matrix is rebuilt on query for simplicity and portability.",
        },
    }
    status_payload = {
        "status": "ok",
        "backend": "tfidf_cosine",
        "example_count": len(rows),
        "optional_sentence_transformers_available": _sentence_transformers_available(),
        "supported_use_cases": [
            "label reviewer support",
            "similar past signals",
            "error analysis slices",
        ],
    }
    write_json(Path(args.index_out), index_payload)
    write_json(Path(args.status_out), status_payload)
    print(json.dumps({"status": "ok", "example_count": len(rows), "index_out": args.index_out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
