from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np


@dataclass(frozen=True)
class RetrievalRecord:
    record_id: str
    case_id: str
    object_type: str
    text: str
    metadata: dict[str, Any]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def _normalize_vectors(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def _hash_embedding(text: str, *, dimensions: int = 256) -> np.ndarray:
    vector = np.zeros(dimensions, dtype=np.float32)
    tokens = _tokenize(text)
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        position = int.from_bytes(digest[:4], byteorder="big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[position] += sign
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector
    return vector / norm


def _sentence_transformer_embeddings(
    texts: list[str],
    *,
    model_name: str,
) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    matrix = np.asarray(model.encode(texts, show_progress_bar=False, normalize_embeddings=True))
    return matrix.astype(np.float32)


def build_embedding_matrix(
    texts: list[str],
    *,
    provider: str = "hashing",
    dimensions: int = 256,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> tuple[np.ndarray, dict[str, Any]]:
    if provider == "sentence_transformers":
        matrix = _sentence_transformer_embeddings(texts, model_name=model_name)
        return matrix, {"provider": provider, "model_name": model_name, "dimensions": int(matrix.shape[1])}

    matrix = np.vstack([_hash_embedding(text, dimensions=dimensions) for text in texts]).astype(np.float32)
    matrix = _normalize_vectors(matrix)
    return matrix, {"provider": "hashing", "dimensions": dimensions}


def write_retrieval_index(
    *,
    output_dir: Path,
    records: list[RetrievalRecord],
    provider: str = "hashing",
    dimensions: int = 256,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    texts = [record.text for record in records]
    matrix, metadata = build_embedding_matrix(
        texts,
        provider=provider,
        dimensions=dimensions,
        model_name=model_name,
    )

    vectors_path = output_dir / "vectors.npy"
    metadata_path = output_dir / "records.json"
    summary_path = output_dir / "index_summary.json"

    np.save(vectors_path, matrix)
    metadata_path.write_text(
        json.dumps(
            [
                {
                    "record_id": record.record_id,
                    "case_id": record.case_id,
                    "object_type": record.object_type,
                    "text": record.text,
                    "metadata": record.metadata,
                }
                for record in records
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(
            {
                **metadata,
                "record_count": len(records),
                "vectors_path": str(vectors_path),
                "records_path": str(metadata_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "vectors_path": vectors_path,
        "records_path": metadata_path,
        "summary_path": summary_path,
    }


def load_retrieval_index(output_dir: Path) -> tuple[np.ndarray, list[dict[str, Any]]]:
    vectors = np.load(output_dir / "vectors.npy")
    records = json.loads((output_dir / "records.json").read_text(encoding="utf-8"))
    return vectors, [row for row in records if isinstance(row, dict)]


def query_retrieval_index(
    *,
    output_dir: Path,
    query: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    vectors, records = load_retrieval_index(output_dir)
    summary = json.loads((output_dir / "index_summary.json").read_text(encoding="utf-8"))
    provider = str(summary.get("provider", "hashing"))
    if provider == "sentence_transformers":
        query_matrix, _ = build_embedding_matrix(
            [query],
            provider=provider,
            model_name=str(summary.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")),
        )
    else:
        query_matrix, _ = build_embedding_matrix(
            [query],
            provider="hashing",
            dimensions=int(summary.get("dimensions", 256)),
        )
    similarities = vectors @ query_matrix[0]
    ranked_indices = np.argsort(similarities)[::-1][: max(1, top_k)]
    return [
        {
            **records[int(index)],
            "similarity": round(float(similarities[int(index)]), 6),
        }
        for index in ranked_indices
    ]
