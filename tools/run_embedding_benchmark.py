#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from experiment_common import GOLD_PATH, gate_state, read_jsonl, row_label, row_text, valid_gold_rows  # noqa: E402


def tokenize(text: str) -> Counter[str]:
    tokens = [token.lower() for token in text.replace("/", " ").replace("-", " ").split()]
    return Counter(token.strip(".,;:!?()[]{}\"'") for token in tokens if len(token.strip(".,;:!?()[]{}\"'")) >= 3)


def cosine(left: Counter[str], right: Counter[str]) -> float:
    common = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def benchmark(rows: list[dict[str, object]], *, k: int) -> dict[str, object]:
    vectors = [tokenize(row_text(row)) for row in rows]
    recall_hits = 0
    agreement_hits = 0
    evaluated = 0
    examples: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        scores = []
        for other_index, other in enumerate(rows):
            if index == other_index:
                continue
            scores.append((cosine(vectors[index], vectors[other_index]), other_index))
        top = sorted(scores, reverse=True)[:k]
        if not top:
            continue
        evaluated += 1
        label = row_label(row)
        neighbor_labels = [row_label(rows[other_index]) for _, other_index in top]
        if label in neighbor_labels:
            recall_hits += 1
        if neighbor_labels and neighbor_labels[0] == label:
            agreement_hits += 1
        examples.append(
            {
                "query_label": label,
                "nearest_labels": neighbor_labels,
                "query_text": row_text(row)[:180],
            }
        )
    return {
        "embedding_backend": "local_bag_of_words_fallback",
        "evaluated_rows": evaluated,
        "k": k,
        "recall_at_k": round(recall_hits / evaluated, 4) if evaluated else 0.0,
        "nearest_neighbor_label_agreement": round(agreement_hits / evaluated, 4) if evaluated else 0.0,
        "examples": examples[:5],
        "note": "This is a local benchmark layer only; embeddings cannot override deterministic outputs.",
    }


def write_report(payload: dict[str, object]) -> None:
    path = ROOT / "reports" / "retrieval_eval.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval / Embedding Evaluation",
        "",
        f"- status: `{payload['status']}`",
        f"- gold_labels: `{payload.get('gold_labels', 0)}`",
        f"- backend: `{payload.get('embedding_backend', 'not_run')}`",
        f"- recall_at_k: `{payload.get('recall_at_k', 'not_run')}`",
        f"- nearest_neighbor_label_agreement: `{payload.get('nearest_neighbor_label_agreement', 'not_run')}`",
        "",
        "Embeddings are benchmark-only and never override deterministic labels.",
    ]
    if payload.get("reason"):
        lines.extend(["", f"Reason: {payload['reason']}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a gated local embedding/retrieval benchmark over gold evidence spans.")
    parser.add_argument("--gold", default=str(GOLD_PATH))
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--enable-retrieval-experiment", action="store_true")
    args = parser.parse_args(argv)

    rows = valid_gold_rows(read_jsonl(Path(args.gold)))
    gates = gate_state(gold_count=len(rows), retrieval_experiment_mode=args.enable_retrieval_experiment)
    if not gates["embeddings"]:
        payload: dict[str, object] = {
            "status": "skipped",
            "gold_labels": len(rows),
            "reason": "Embeddings require >=100 gold labels or --enable-retrieval-experiment.",
        }
        write_report(payload)
        print(json.dumps(payload, indent=2))
        return 0
    if len(rows) < 2:
        payload = {"status": "skipped", "gold_labels": len(rows), "reason": "At least two valid gold evidence spans are required."}
        write_report(payload)
        print(json.dumps(payload, indent=2))
        return 0
    payload = {"status": "completed", "gold_labels": len(rows), **benchmark(rows, k=args.k)}
    write_report(payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
