from __future__ import annotations

from pathlib import Path

import pytest

from signal_engine.retrieval.evaluate import validate_no_forbidden_payload_keys


def test_retrieval_manifests_do_not_expose_raw_text_column() -> None:
    header = Path("data/retrieval/retrieval_objects_manifest.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "evidence_text" not in header
    assert "raw_text_committed" in header


@pytest.mark.parametrize(
    "forbidden_key",
    ["raw_text", "transcript_text", "asr_text", "audio_text", "chunk_text", "embedding", "embeddings", "vector", "vectors", "vector_db", "payload_text"],
)
def test_forbidden_raw_payload_keys_fail(forbidden_key: str) -> None:
    errors = validate_no_forbidden_payload_keys({forbidden_key: "blocked"}, context="result")
    assert errors
    assert forbidden_key in errors[0]
