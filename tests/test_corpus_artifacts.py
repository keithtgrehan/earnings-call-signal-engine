from __future__ import annotations

import pandas as pd

from earnings_call_sentiment.corpus_artifacts import (
    _build_event_chunks,
    _build_evidence_objects,
    _build_qa_pairs,
    _build_segment_rows,
    _build_transcript_blocks,
)


def test_event_export_builds_qa_pairs_and_chunks() -> None:
    segments = [
        {
            "start": 0.0,
            "end": 12.0,
            "text": "Operator: Welcome to the call. We will now begin the question and answer session.",
        },
        {
            "start": 12.0,
            "end": 24.0,
            "text": "Can you talk about revenue guidance and margin pressure for next quarter?",
        },
        {
            "start": 24.0,
            "end": 36.0,
            "text": "We expect revenue growth to continue and we remain comfortable with the full-year outlook.",
        },
    ]
    guidance_df = pd.DataFrame(
        [{"start": 24.0, "end": 36.0, "text": "remain comfortable with the full-year outlook", "topic": "outlook", "period": "full_year"}]
    )
    uncertainty_df = pd.DataFrame()
    skepticism_df = pd.DataFrame([{"text": "margin pressure"}])

    segment_rows = _build_segment_rows(
        segments,
        source_doc="transcript_json",
        guidance_df=guidance_df,
        uncertainty_df=uncertainty_df,
        skepticism_df=skepticism_df,
    )
    blocks = _build_transcript_blocks(segment_rows)
    qa_pairs = _build_qa_pairs(blocks)
    event_chunks = _build_event_chunks(
        case_id="TEST_2026_Q1_call01",
        segment_rows=segment_rows,
        chunks_scored_df=pd.DataFrame(),
    )

    assert len(qa_pairs) == 1
    assert qa_pairs[0]["question_text"]
    assert any(chunk["event_type"] == "qa_question" for chunk in event_chunks)
    assert any(chunk["guidance_related"] for chunk in event_chunks)

    evidence_objects = _build_evidence_objects(
        case_id="TEST_2026_Q1_call01",
        company="Test Co",
        ticker="TEST",
        fiscal_period="Q1_2026",
        event_date="2026-01-30",
        transcript_source_type="local_asr_transcript",
        blocks=blocks,
        qa_pairs=qa_pairs,
        event_chunks=event_chunks,
        guidance_df=guidance_df,
        uncertainty_df=uncertainty_df,
        reassurance_df=pd.DataFrame(),
        skepticism_df=skepticism_df,
        source_paths={
            "segment_metadata": "segment_metadata.json",
            "transcript_sectioned": "transcript_sectioned.json",
            "qa_pairs": "qa_pairs.json",
            "event_chunks": "event_chunks.jsonl",
            "guidance": "guidance.csv",
            "uncertainty": "",
            "reassurance": "",
            "skepticism": "analyst_skepticism.csv",
        },
    )

    assert any(row["object_type"] == "guidance_span" for row in evidence_objects)
    assert any(row["object_type"] == "qa_answer" for row in evidence_objects)
