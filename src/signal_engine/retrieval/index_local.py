from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(value: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(value)]


def object_tokens(row: dict[str, str]) -> list[str]:
    fields = ["ticker", "section", "speaker", "topic", "rights_tier", "object_type", "case_id"]
    return tokenize(" ".join(str(row.get(field, "")) for field in fields))


def load_retrieval_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_local_bm25_index(objects: list[dict[str, str]], *, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    docs: list[dict[str, Any]] = []
    document_frequency: Counter[str] = Counter()
    for row in objects:
        tokens = object_tokens(row)
        counts = Counter(tokens)
        document_frequency.update(counts.keys())
        docs.append({"object_id": row.get("object_id", ""), "tokens": dict(counts), "length": len(tokens), "metadata": row})
    payload = {
        "index_version": "local_bm25_metadata_v1",
        "document_count": len(docs),
        "avg_doc_length": (sum(doc["length"] for doc in docs) / len(docs)) if docs else 0.0,
        "document_frequency": dict(document_frequency),
        "documents": docs,
        "raw_text_indexed": False,
        "embeddings_enabled": False,
        "vector_db_committed": False,
    }
    (out_dir / "index.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def score_query(index: dict[str, Any], query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    tokens = tokenize(query)
    if not tokens:
        return []
    docs = index.get("documents", [])
    n_docs = max(1, int(index.get("document_count") or len(docs) or 1))
    avgdl = float(index.get("avg_doc_length") or 1.0) or 1.0
    df = index.get("document_frequency", {})
    k1 = 1.2
    b = 0.75
    results: list[dict[str, Any]] = []
    for doc in docs:
        counts = doc.get("tokens", {})
        dl = float(doc.get("length") or 0.0) or 1.0
        score = 0.0
        for token in tokens:
            tf = float(counts.get(token, 0))
            if tf <= 0:
                continue
            idf = math.log(1 + (n_docs - float(df.get(token, 0)) + 0.5) / (float(df.get(token, 0)) + 0.5))
            score += idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl)))
        if score > 0:
            results.append({"object_id": doc.get("object_id", ""), "score": score, "metadata": doc.get("metadata", {})})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]
