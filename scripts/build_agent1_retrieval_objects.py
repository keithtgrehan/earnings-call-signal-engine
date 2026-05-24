#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build retrieval-readiness evidence objects from Agent 1 candidates without embeddings.")
    parser.add_argument("--candidates", default="data/review/staging/agent1_candidates_deduped.jsonl")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--out", default="data/review/staging/agent1_retrieval_objects.jsonl")
    parser.add_argument("--report", default="reports/retrieval_readiness_30.md")
    args = parser.parse_args(argv)
    registry = {str(row.get("source_path_ref")): row for row in _load_jsonl(Path(args.registry)) if str(row.get("source_sha256", "")).startswith("sha256:")}
    objects = []
    for row in _load_jsonl(Path(args.candidates)):
        source_file = str(row.get("source_file", ""))
        if source_file not in registry:
            continue
        objects.append(
            {
                "object_id": row.get("candidate_id"),
                "case_id": row.get("case_id"),
                "object_type": "evidence_object",
                "source_file": source_file,
                "source_sha256": row.get("source_sha256"),
                "evidence_span_ref": row.get("evidence_span_ref"),
                "text_hash": row.get("text_hash"),
                "redacted_preview": row.get("redacted_preview", ""),
                "raw_text_commit_allowed": False,
                "embedding_built": False,
                "vector_db_written": False,
                "provenance_hash": row.get("provenance_hash"),
            }
        )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for obj in objects:
            handle.write(json.dumps(obj, sort_keys=True) + "\n")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# Retrieval Readiness 30",
                "",
                "- Evidence objects first.",
                "- Event-aligned chunks second.",
                "- Semantic chunks third.",
                f"- Evidence objects built: `{len(objects)}`",
                "- Embeddings built: `false`",
                "- Vector DB written: `false`",
                "- Full raw text committed: `false`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Agent 1 retrieval objects written: {len(objects)} object(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
