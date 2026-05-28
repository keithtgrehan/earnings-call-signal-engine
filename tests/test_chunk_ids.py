from __future__ import annotations

from signal_engine.chunking import stable_chunk_id


def test_chunk_ids_are_stable() -> None:
    assert stable_chunk_id("CASE1", "qa_pair", 10, 20) == stable_chunk_id("CASE1", "qa_pair", 10, 20)
    assert stable_chunk_id("CASE1", "qa_pair", 10, 20) != stable_chunk_id("CASE1", "qa_pair", 10, 21)
