from __future__ import annotations

from pathlib import Path

from earnings_call_sentiment.retrieval_index import (
    RetrievalRecord,
    query_retrieval_index,
    write_retrieval_index,
)


def test_retrieval_index_writes_and_queries(tmp_path: Path) -> None:
    output_dir = tmp_path / "index"
    write_retrieval_index(
        output_dir=output_dir,
        records=[
            RetrievalRecord(
                record_id="row1",
                case_id="TEST_01",
                object_type="guidance_span",
                text="We raised revenue guidance for the full year.",
                metadata={"ticker": "TEST"},
            ),
            RetrievalRecord(
                record_id="row2",
                case_id="TEST_02",
                object_type="event_chunk",
                text="Operating margin faced pressure in Europe.",
                metadata={"ticker": "ALT"},
            ),
        ],
        provider="hashing",
    )

    results = query_retrieval_index(output_dir=output_dir, query="revenue guidance", top_k=1)

    assert len(results) == 1
    assert results[0]["record_id"] == "row1"
