from __future__ import annotations

from signal_engine.chunking import build_event_chunks_for_text


def test_event_chunker_emits_event_types_without_committed_text_fields() -> None:
    text = "Prepared remarks\nCEO: We narrowed guidance.\nQuestion-and-Answer\nAnalyst: Question?\nCFO: Answer."
    chunks = build_event_chunks_for_text(text, case_id="case1_2025_q1", ticker="JPM", source_sha256="sha256:" + "a" * 64)
    types = {chunk["chunk_type"] for chunk in chunks}

    assert {"guidance_revision_candidate", "qa_question", "qa_answer", "qa_pair"}.issubset(types)
    manifest_like = [{key: value for key, value in chunk.items() if key != "_text"} for chunk in chunks]
    assert "narrowed guidance" not in str(manifest_like)
    assert all(chunk["raw_text_committed"] == "false" for chunk in chunks)


def test_event_chunker_uses_semantic_fallback_when_no_markers() -> None:
    chunks = build_event_chunks_for_text("plain words only", case_id="case1", ticker="JPM", source_sha256="sha256:" + "b" * 64)

    assert chunks[0]["chunk_type"] == "semantic_fallback"
