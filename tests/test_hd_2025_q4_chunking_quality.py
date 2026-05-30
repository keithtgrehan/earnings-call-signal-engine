from __future__ import annotations

from pathlib import Path

from signal_engine.chunking.event_chunker import build_event_chunks_for_text, chunk_quality_summary


def test_normal_length_hd_control_does_not_collapse_to_one_chunk() -> None:
    path = Path("/Users/keith/Desktop/earnings calls 100 samples/HD_The_Home_Depot_Inc/hd_2025_q4/transcript/hd_2025_q4_40a000cd.txt")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = build_event_chunks_for_text(text, case_id="hd_2025_q4", ticker="HD", source_sha256="sha256:" + "a" * 64)
    quality = chunk_quality_summary(text, chunks)
    assert len(chunks) > 1
    assert quality["large_chunk_warning"] is False
    assert quality["raw_text_leak_check"] == "passed"
