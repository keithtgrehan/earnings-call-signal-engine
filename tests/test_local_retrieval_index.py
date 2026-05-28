from __future__ import annotations

from pathlib import Path

from signal_engine.retrieval.index_local import build_local_bm25_index
from signal_engine.retrieval.query import query_local_index


def test_local_retrieval_index_uses_metadata_tokens_only(tmp_path: Path) -> None:
    objects = [
        {
            "object_id": "obj1",
            "ticker": "JPM",
            "section": "qa",
            "speaker": "management",
            "topic": "qa_pair",
            "rights_tier": "safe_to_download",
            "object_type": "event_aligned_chunk",
            "case_id": "case1",
        }
    ]

    index = build_local_bm25_index(objects, out_dir=tmp_path / "index")
    results = query_local_index(tmp_path / "index", "qa management")

    assert index["raw_text_indexed"] is False
    assert index["embeddings_enabled"] is False
    assert results[0]["object_id"] == "obj1"
