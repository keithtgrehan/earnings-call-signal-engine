#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluation_quality import EVIDENCE_OBJECTS_PATH, read_jsonl  # noqa: E402

MODEL_MAP = {
    "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "all-mpnet-base-v2": "sentence-transformers/all-mpnet-base-v2",
    "bge-small-en": "BAAI/bge-small-en-v1.5",
}


def write_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Retrieval Benchmark",
        "",
        f"- status: `{payload['status']}`",
        f"- evidence_objects: `{payload.get('evidence_objects', 0)}`",
        f"- backend: `{payload.get('backend', 'not_run')}`",
        f"- model: `{payload.get('model', 'not_run')}`",
        f"- recall_at_k: `{payload.get('recall_at_k', 'not_run')}`",
        f"- nearest_neighbor_agreement: `{payload.get('nearest_neighbor_agreement', 'not_run')}`",
        "",
        "Embeddings are benchmark-only. Retrieval does not alter deterministic outputs.",
    ]
    if payload.get("reason"):
        lines.extend(["", f"Reason: {payload['reason']}"])
    if payload.get("examples"):
        lines.extend(["", "## Examples", ""])
        for item in payload["examples"]:
            lines.append(
                f"- query=`{item['query_label']}` nearest=`{item['nearest_labels']}` text={item['query_text'][:140]}"
            )
    (ROOT / "reports" / "retrieval_benchmark.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def run_benchmark(rows: list[dict[str, Any]], *, model_key: str, k: int) -> dict[str, Any]:
    try:
        import faiss
    except Exception as exc:
        return {"status": "skipped", "reason": f"FAISS unavailable: {exc}", "evidence_objects": len(rows)}
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:
        return {"status": "skipped", "reason": f"sentence-transformers unavailable: {exc}", "evidence_objects": len(rows)}

    model_name = MODEL_MAP[model_key]
    try:
        model = SentenceTransformer(model_name, local_files_only=True)
    except Exception as exc:
        return {
            "status": "skipped",
            "reason": f"Local model unavailable for {model_name}; no download attempted: {exc}",
            "evidence_objects": len(rows),
            "model": model_key,
        }

    texts = [str(row["text"]) for row in rows]
    labels = [str(row["gold_label"]) for row in rows]
    embeddings = np.asarray(model.encode(texts, show_progress_bar=False, normalize_embeddings=True), dtype="float32")
    embeddings = normalize(embeddings)
    index = faiss.IndexFlatIP(int(embeddings.shape[1]))
    index.add(embeddings)
    search_k = min(k + 1, len(rows))
    _, indices = index.search(embeddings, search_k)

    recall_hits = 0
    agreement_hits = 0
    examples: list[dict[str, Any]] = []
    for row_index, neighbors in enumerate(indices.tolist()):
        neighbor_indices = [index for index in neighbors if index != row_index][:k]
        neighbor_labels = [labels[index] for index in neighbor_indices]
        if labels[row_index] in neighbor_labels:
            recall_hits += 1
        if neighbor_labels and neighbor_labels[0] == labels[row_index]:
            agreement_hits += 1
        if len(examples) < 5:
            examples.append(
                {
                    "query_label": labels[row_index],
                    "nearest_labels": neighbor_labels,
                    "query_text": texts[row_index],
                }
            )
    evaluated = len(rows)
    return {
        "status": "completed",
        "evidence_objects": len(rows),
        "backend": "faiss_inner_product",
        "model": model_key,
        "k": k,
        "recall_at_k": round(recall_hits / evaluated, 4) if evaluated else 0.0,
        "nearest_neighbor_agreement": round(agreement_hits / evaluated, 4) if evaluated else 0.0,
        "examples": examples,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a gated local retrieval benchmark over evidence objects.")
    parser.add_argument("--evidence", default=str(EVIDENCE_OBJECTS_PATH))
    parser.add_argument("--model", choices=sorted(MODEL_MAP), default="all-MiniLM-L6-v2")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--enable-retrieval-experiment", action="store_true")
    args = parser.parse_args(argv)
    rows = read_jsonl(Path(args.evidence))
    if len(rows) < 100 and not args.enable_retrieval_experiment:
        payload = {
            "status": "skipped",
            "evidence_objects": len(rows),
            "reason": "Retrieval benchmark requires >=100 labels or --enable-retrieval-experiment.",
        }
        write_report(payload)
        print(json.dumps(payload, indent=2))
        return 0
    if len(rows) < 2:
        payload = {"status": "skipped", "evidence_objects": len(rows), "reason": "At least two evidence objects are required."}
        write_report(payload)
        print(json.dumps(payload, indent=2))
        return 0
    payload = run_benchmark(rows, model_key=args.model, k=max(1, args.k))
    write_report(payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
