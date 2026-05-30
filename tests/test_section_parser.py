from __future__ import annotations

from signal_engine.chunking.section_parser import section_spans


def test_section_parser_detects_prepared_and_qa_spans() -> None:
    spans = section_spans("Intro\nPrepared remarks\nCEO: hello\nQuestion-and-Answer\nAnalyst: question")
    labels = [span["section_type"] for span in spans]

    assert "prepared_remarks" in labels
    assert "qna" in labels
