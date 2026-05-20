#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from review.chunking import read_jsonl, write_jsonl  # noqa: E402
from review.storage import INSTALL_GUIDANCE  # noqa: E402
from review.suggestions import build_suggestions, suggestions_by_chunk  # noqa: E402


def _upload_argilla(dataset_name: str, rows: list[dict[str, object]], records_path: Path) -> int:
    try:
        import argilla as rg  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Argilla suggestion upload requested but Argilla is not installed. {INSTALL_GUIDANCE}") from exc
    client = rg.Argilla(
        api_url=os.environ.get("ARGILLA_API_URL", "http://localhost:6900"),
        api_key=os.environ.get("ARGILLA_API_KEY", "argilla.apikey"),
    )
    dataset = client.datasets(name=dataset_name, workspace=os.environ.get("ARGILLA_WORKSPACE", "signal-engine"))
    if dataset is None:
        raise SystemExit("Argilla dataset not found. Run make review-bootstrap first.")
    records = read_jsonl(records_path)
    grouped = suggestions_by_chunk(rows)
    argilla_records = []
    for record in records:
        chunk_id = str(record.get("chunk_id") or record.get("external_id") or "")
        chunk_suggestions = grouped.get(chunk_id, [])
        if not chunk_suggestions:
            continue
        labels = sorted({str(item.get("label")) for item in chunk_suggestions if item.get("label")})
        if not labels:
            continue
        score = min(float(item.get("confidence") or 0.0) for item in chunk_suggestions)
        suggestion = rg.Suggestion(question_name="signals", value=labels, score=score)
        argilla_records.append(
            rg.Record(
                fields={"text": record.get("text", "")},
                metadata={**dict(record.get("metadata") or {}), "review_state": "suggested"},
                suggestions=[suggestion],
                external_id=chunk_id,
            )
        )
    if argilla_records:
        dataset.records.log(argilla_records)
    return len(argilla_records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map deterministic weak labels into Argilla suggestion JSONL.")
    parser.add_argument("--weak-labels", default=str(ROOT / "data" / "corpus" / "processed" / "chunks" / "LLY_2025_Q2_call08.event_chunks.jsonl"))
    parser.add_argument("--records", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "argilla_records.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "argilla_suggestions.jsonl"))
    parser.add_argument("--dataset", default=os.environ.get("ARGILLA_DATASET", "earnings-call-review"))
    parser.add_argument("--min-confidence", type=float, default=0.6)
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args(argv)
    rows = read_jsonl(Path(args.weak_labels))
    suggestions = [item.to_record() for item in build_suggestions(rows, min_confidence=args.min_confidence)]
    write_jsonl(Path(args.out), suggestions)
    uploaded = _upload_argilla(args.dataset, suggestions, Path(args.records)) if args.upload else 0
    print(json.dumps({"suggestions": len(suggestions), "output": args.out, "uploaded": uploaded}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
