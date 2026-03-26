from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from earnings_call_sentiment.model_sidecars.io import (
    load_units_for_case,
    resolve_case_artifacts,
    write_classification_outputs,
)
from earnings_call_sentiment.model_sidecars.models.base import (
    ClassificationOutput,
    LabelScore,
    TextUnit,
)


def _build_case_dir(tmp_path: Path) -> Path:
    case_dir = tmp_path / "case"
    case_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Prepared remarks remain solid.",
                "sentiment": "POSITIVE",
                "score": 0.95,
                "signed_score": 0.95,
            }
        ]
    ).to_csv(case_dir / "chunks_scored.csv", index=False)

    pd.DataFrame(
        [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "We expect margin pressure to ease.",
                "topic": "margin",
                "period": "FY",
                "guidance_strength": 0.7,
                "matched_cues": "we expect;margin",
            }
        ]
    ).to_csv(case_dir / "guidance.csv", index=False)

    pd.DataFrame(
        [
            {
                "row_id": "row-1",
                "topic": "margin",
                "period": "FY",
                "revision_label": "maintained",
                "current_text_snippet": "We expect margin pressure to ease.",
                "prior_text_snippet": "Margin pressure should moderate.",
            }
        ]
    ).to_csv(case_dir / "guidance_revision.csv", index=False)

    (case_dir / "qa_pairs.json").write_text(
        json.dumps(
            {
                "qa_pairs": [
                    {
                        "qa_pair_id": 1,
                        "question_speaker": "Analyst One",
                        "question_text": "Can you clarify demand trends?",
                        "answer_speakers": ["CFO"],
                        "answer_text": "We are seeing stable demand and better visibility.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    (case_dir / "transcript_sectioned.json").write_text(
        json.dumps(
            {
                "blocks": [
                    {
                        "block_id": 0,
                        "section": "presentation",
                        "speaker": "CEO",
                        "speaker_role": "management",
                        "timestamp": "00:00",
                        "text": "Prepared remarks remain solid.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    (case_dir / "segment_metadata.json").write_text(
        json.dumps(
            {
                "segments": [
                    {
                        "segment_id": 7,
                        "section": "presentation",
                        "speaker": "CEO",
                        "speaker_role": "management",
                        "start": 0.0,
                        "end": 5.0,
                        "text": "Prepared remarks remain solid.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return case_dir


def test_load_units_for_case_reuses_existing_artifacts(tmp_path: Path) -> None:
    case_dir = _build_case_dir(tmp_path)
    case = resolve_case_artifacts("synthetic_case", case_dir=case_dir)

    units = load_units_for_case(
        case,
        unit_types=["chunks", "guidance_spans", "qa_answers", "speaker_turns"],
    )

    assert units["chunks"][0].source_id == "7"
    assert units["guidance_spans"][0].speaker == "CEO"
    assert units["qa_answers"][0].speaker == "CFO"
    assert units["speaker_turns"][0].speaker == "CEO"


def test_write_classification_outputs_writes_expected_schema(tmp_path: Path) -> None:
    output_root = tmp_path / "outputs" / "synthetic_case" / "model_sidecars"
    unit = TextUnit(
        case_id="synthetic_case",
        unit_type="chunks",
        source_id="chunk-1",
        text="Demand remains stable.",
        section="presentation",
        speaker="CEO",
        metadata={"topic": "demand"},
    )
    outputs = {
        "chunks": [
            ClassificationOutput(
                unit=unit,
                scores=[
                    LabelScore(label="positive", score=0.9, rank=1),
                    LabelScore(label="neutral", score=0.1, rank=2),
                ],
            )
        ]
    }

    artifacts = write_classification_outputs(
        case_id="synthetic_case",
        model_name="finbert_tone",
        model_id="model-id",
        output_root=output_root,
        outputs_by_unit=outputs,
        runtime_s=1.23,
    )

    lines = (artifacts["chunks"]).read_text(encoding="utf-8").strip().splitlines()
    row = json.loads(lines[0])
    assert row["case_id"] == "synthetic_case"
    assert row["unit_type"] == "chunks"
    assert row["source_id"] == "chunk-1"
    assert row["model_name"] == "finbert_tone"
    assert row["label"] == "positive"
    assert row["rank"] == 1
    assert row["metadata"]["source_metadata"]["topic"] == "demand"
