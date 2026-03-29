from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.nlp_sidecars.base import ClassificationResult, LabelScore
from earnings_call_sentiment.nlp_sidecars.io import build_artifact_inputs
from earnings_call_sentiment.nlp_sidecars.runner import run_sidecar_models


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


class _FakeClassificationModel:
    output_kind = "classification"

    def prewarm(self) -> dict[str, str]:
        return {"device": "cpu", "task": "text-classification"}

    def predict(self, units, *, batch_size, max_length, label_groups=None):
        del batch_size, max_length, label_groups
        return [
            ClassificationResult(
                unit=unit,
                scores=[
                    LabelScore(label="positive", score=0.91, rank=1),
                    LabelScore(label="neutral", score=0.09, rank=2),
                ],
                comparable_label="positive",
            )
            for unit in units
        ]


class _FailingModel:
    output_kind = "classification"

    def prewarm(self):
        raise RuntimeError("Optional dependency 'transformers' is not available. Install 'transformers' to enable this sidecar.")


def test_run_sidecar_models_writes_outputs_and_evaluation(tmp_path: Path, monkeypatch) -> None:
    demo_case_root = _build_demo_case_root(tmp_path)
    artifact_inputs = build_artifact_inputs(case_id="demo_case", demo_case_root=demo_case_root)

    monkeypatch.setattr(
        "earnings_call_sentiment.nlp_sidecars.runner.build_model",
        lambda name, device, cache_dir: _FakeClassificationModel(),
    )

    payload = run_sidecar_models(
        case_id="demo_case",
        artifact_inputs=artifact_inputs,
        unit_types=["chunks", "guidance_spans", "qa_answers"],
        model_names=["finbert_tone", "financial_roberta"],
        output_root=tmp_path / "outputs",
        zero_shot_config=None,
    )

    assert payload["units_loaded"] == 3
    assert len(payload["models"]) == 2
    first_summary = tmp_path / "outputs" / "demo_case" / "model_sidecars" / "finbert_tone" / "run_summary.json"
    assert first_summary.exists()
    evaluation = tmp_path / "outputs" / "demo_case" / "model_sidecars" / "evaluation" / "comparison_summary.json"
    assert evaluation.exists()


def test_run_sidecar_models_records_graceful_failure(tmp_path: Path, monkeypatch) -> None:
    demo_case_root = _build_demo_case_root(tmp_path)
    artifact_inputs = build_artifact_inputs(case_id="demo_case", demo_case_root=demo_case_root)

    monkeypatch.setattr(
        "earnings_call_sentiment.nlp_sidecars.runner.build_model",
        lambda name, device, cache_dir: _FailingModel(),
    )

    payload = run_sidecar_models(
        case_id="demo_case",
        artifact_inputs=artifact_inputs,
        unit_types=["chunks"],
        model_names=["finbert_tone"],
        output_root=tmp_path / "outputs",
        zero_shot_config=None,
    )

    assert payload["models"][0]["status"] == "error"
    summary_path = tmp_path / "outputs" / "demo_case" / "model_sidecars" / "finbert_tone" / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "error"
    assert "Deterministic transcript-backed outputs remain canonical." in summary["notes"]
