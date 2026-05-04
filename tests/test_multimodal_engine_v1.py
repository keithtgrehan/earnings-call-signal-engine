from __future__ import annotations

from pathlib import Path

from active_learning import select_review_batch
from alignment import align_records
from audio_engine import extract_audio_features
from data_layer import DATASET_CONNECTORS, NormalizedRecord, Provenance, ingest_datasets, normalize_domain
from ensemble import build_ensemble_outputs
from fusion import fuse_modalities
from text_engine import score_text_segments
from training import evaluate_outputs, train_models
from video_engine import extract_video_features


def test_normalized_schema_accepts_required_contract() -> None:
    record = NormalizedRecord(
        id="case-1",
        text="We are concerned this may slip.",
        emotion="concern",
        sentiment="negative",
        domain=normalize_domain("earnings_call"),
        source="unit_test",
        provenance=Provenance.human_gold,
    )

    payload = record.to_json_dict()
    assert payload["id"] == "case-1"
    assert payload["domain"] == "earnings"
    assert payload["provenance"] == "human_gold"


def test_ingestion_records_all_requested_dataset_connectors(tmp_path: Path) -> None:
    result = ingest_datasets(output_dir=tmp_path, dry_run=True)
    statuses = {item["dataset_id"]: item for item in result["manifest"]["dataset_statuses"]}

    assert set(statuses) == {connector.dataset_id for connector in DATASET_CONNECTORS}
    assert statuses["earnings_call_transcripts"]["status"] == "completed"
    assert statuses["IEMOCAP"]["status"] == "skipped"
    assert result["manifest"]["loaded_rows"] > 0


def test_stage_functions_produce_transparent_outputs(tmp_path: Path) -> None:
    records = [
        NormalizedRecord(
            id="support-risk-1",
            text="I am frustrated this is still unresolved and need an answer today.",
            domain="support",
            source="unit_test",
            provenance=Provenance.synthetic,
        )
    ]

    aligned = align_records(records, output_dir=tmp_path)
    segments = aligned["segments"]
    text = score_text_segments(segments, output_dir=tmp_path)
    audio = extract_audio_features(segments, output_dir=tmp_path)
    video = extract_video_features(segments, text_rows=text["rows"], output_dir=tmp_path)
    fused = fuse_modalities(
        text_rows=text["rows"],
        audio_rows=audio["rows"],
        video_rows=video["rows"],
        output_dir=tmp_path,
    )
    ensemble = build_ensemble_outputs(text_rows=text["rows"], fusion_rows=fused["rows"], output_dir=tmp_path)
    active = select_review_batch(ensemble["rows"], output_dir=tmp_path)
    evaluation = evaluate_outputs(ensemble_rows=ensemble["rows"], output_dir=tmp_path)

    assert segments[0].segment_id == "support-risk-1:segment:0"
    assert text["rows"][0]["rule_signal"] == "risk_friction"
    assert audio["rows"][0]["available"] is False
    assert video["rows"][0]["flagged_for_video"] is True
    assert fused["rows"][0]["text_anchor_signal"] == "risk_friction"
    assert ensemble["rows"][0]["model_votes"]["rule"] == "risk_friction"
    assert active["rows"]
    assert evaluation["report"]["metric_scope"].startswith("self-consistency")


def test_training_dry_run_reports_readiness_without_writing_models(tmp_path: Path) -> None:
    result = train_models(output_dir=tmp_path, model_dir=tmp_path / "models", dry_run=True)

    assert result["summary"]["stage"] == "train"
    assert "readiness" in result["summary"]
    assert not (tmp_path / "models" / "text_signal_baseline.joblib").exists()
