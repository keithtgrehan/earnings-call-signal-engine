from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.nlp_sidecars.io import build_artifact_inputs, load_text_units


def _build_demo_case_root(tmp_path: Path) -> Path:
    root = tmp_path / "demo_case"
    (root / "processed" / "chunks").mkdir(parents=True)
    (root / "processed" / "signals").mkdir(parents=True)
    (root / "processed" / "qa_pairs").mkdir(parents=True)
    (root / "processed" / "chunks" / "chunks_scored.csv").write_text(
        "start,end,text,sentiment,score,signed_score\n"
        "0,10,Prepared remarks were cautious.,NEGATIVE,0.9,-0.9\n",
        encoding="utf-8",
    )
    (root / "processed" / "signals" / "guidance.csv").write_text(
        "start,end,text,sentiment,score,topic,period,guidance_strength,matched_cues\n"
        '10,20,"We expect margin pressure to ease later in the year.",POSITIVE,0.8,margin,Q4,0.7,"we expect;q4"\n',
        encoding="utf-8",
    )
    (root / "processed" / "qa_pairs" / "qa_pairs.json").write_text(
        json.dumps(
            [
                {
                    "qa_pair_id": 1,
                    "source_doc": "main_transcript",
                    "question_speaker": "Analyst",
                    "question_text": "What changed?",
                    "answer_speakers": ["CEO"],
                    "answer_text": "We remain careful on near-term demand.",
                }
            ]
        ),
        encoding="utf-8",
    )
    return root


def test_build_artifact_inputs_and_load_units_from_demo_case(tmp_path: Path) -> None:
    demo_case_root = _build_demo_case_root(tmp_path)

    artifact_inputs = build_artifact_inputs(
        case_id="demo_case",
        demo_case_root=demo_case_root,
    )
    units = load_text_units(
        case_id="demo_case",
        artifact_inputs=artifact_inputs,
        unit_types=["chunks", "guidance_spans", "qa_answers"],
    )

    assert sorted(artifact_inputs) == ["chunks", "guidance_spans", "qa_answers"]
    assert [unit.unit_type for unit in units] == ["chunks", "guidance_spans", "qa_answers"]
    assert units[0].deterministic_label == "NEGATIVE"
    assert units[1].deterministic_metadata["topic"] == "margin"
    assert units[2].deterministic_metadata["question_speaker"] == "Analyst"


def test_load_text_units_respects_smoke_limit(tmp_path: Path) -> None:
    demo_case_root = _build_demo_case_root(tmp_path)
    artifact_inputs = build_artifact_inputs(case_id="demo_case", demo_case_root=demo_case_root)

    units = load_text_units(
        case_id="demo_case",
        artifact_inputs=artifact_inputs,
        unit_types=["chunks", "guidance_spans", "qa_answers"],
        smoke_limit=1,
    )

    assert len(units) == 3
