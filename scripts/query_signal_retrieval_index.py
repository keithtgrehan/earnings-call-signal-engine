#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_index(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _query_with_tfidf(examples: list[dict], query: str, top_k: int) -> list[dict]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    texts = [example["text"] for example in examples]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(texts + [query])
    example_matrix = matrix[:-1]
    query_vector = matrix[-1]
    scores = cosine_similarity(example_matrix, query_vector).ravel()
    ranked = sorted(zip(examples, scores, strict=True), key=lambda item: item[1], reverse=True)[:top_k]
    return [
        {
            "id": example["id"],
            "signal_family": example["signal_family"],
            "text": example["text"],
            "evidence_terms": example.get("evidence_terms", []),
            "domain": example.get("domain"),
            "source_file": example.get("source_file"),
            "similarity_score": round(float(score), 4),
        }
        for example, score in ranked
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query the lightweight signal retrieval scaffold.")
    parser.add_argument(
        "--index-path",
        default=str(ROOT / "data" / "nlp_research" / "signal_retrieval_index.json"),
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)

    index_payload = _load_index(Path(args.index_path))
    results = _query_with_tfidf(list(index_payload["examples"]), args.query, max(1, args.top_k))
    print(json.dumps({"status": "ok", "backend": index_payload["backend"], "query": args.query, "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
