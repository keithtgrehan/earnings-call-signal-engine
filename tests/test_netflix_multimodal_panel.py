from __future__ import annotations

import importlib.util
from pathlib import Path

import earnings_call_sentiment.netflix_multimodal_panel as netflix_panel
import pandas as pd
from earnings_call_sentiment.netflix_multimodal_panel import (
    _render_panel_markdown,
    build_audio_support,
    build_curated_moment_manifest,
    build_panel_payload,
    build_visual_support,
    write_curated_sidecar_inputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_curated_moment_manifest_has_expected_showcase_shape() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)

    assert manifest["case_id"] == "netflix_q1_2022"
    assert 8 <= manifest["primary_moment_count"] <= 20
    assert manifest["showcase_moment_count"] == 8
    moment_ids = [row["moment_id"] for row in manifest["moments"]]
    assert "qa_growth_headwinds" in moment_ids
    assert "guidance_negative_q2_net_adds" in moment_ids
    assert moment_ids[:2] == ["qa_growth_headwinds", "qa_q1_miss_explanation"]


def test_write_curated_sidecar_inputs_preserves_manifest_ids(tmp_path: Path) -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    paths = write_curated_sidecar_inputs(manifest, output_dir=tmp_path)

    chunks_text = paths["chunks"].read_text(encoding="utf-8")
    guidance_text = paths["guidance_spans"].read_text(encoding="utf-8")
    qa_text = paths["qa_answers"].read_text(encoding="utf-8")

    assert "chunk_monetize_sharing_competition" in chunks_text
    assert "guidance_negative_q2_net_adds" in guidance_text
    assert "qa_growth_headwinds" in qa_text


def test_build_audio_support_marks_only_curated_rows_as_aligned() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    payload = build_audio_support(manifest, root=REPO_ROOT)

    aligned = [row for row in payload["moments"] if row["status"] == "aligned"]
    unavailable = [row for row in payload["moments"] if row["status"] == "unavailable"]

    assert payload["audio_available"] is True
    assert len(aligned) == 3
    assert len(unavailable) >= 1


def test_build_visual_support_skips_cleanly_when_video_missing(monkeypatch) -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    monkeypatch.setattr(netflix_panel, "REQUESTED_VIDEO_PATH", Path("/tmp/netflix-video-missing-requested.mp4"))
    monkeypatch.setattr(netflix_panel, "FALLBACK_VIDEO_PATH", Path("/tmp/netflix-video-missing-fallback.mp4"))
    payload, skipped = build_visual_support(
        manifest,
        root=REPO_ROOT,
        video_path="/tmp/netflix-video-missing.mp4",
        sample_fps=0.25,
    )

    assert skipped is True
    assert payload["status"] == "skipped"


def test_build_panel_payload_returns_pressure_rows() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    comparison_payload = {
        "moment_rows": [
            {
                "moment_id": "qa_growth_headwinds",
                "consensus_label": "negative",
                "pairwise_disagreement": False,
                "deterministic_alignment": "aligned_with_expected_category",
            },
            {
                "moment_id": "qa_q1_miss_explanation",
                "consensus_label": "negative",
                "pairwise_disagreement": True,
                "deterministic_alignment": "mixed_vs_expected_category",
            },
        ]
    }
    disagreement_payload = {
        "pairwise_model_disagreements": [
            {
                "moment_id": "qa_q1_miss_explanation",
                "quote_or_span": "A disagreement hotspot.",
                "alignment": "mixed_vs_expected_category",
            }
        ]
    }
    audio_payload = {
        "moments": [
            {"moment_id": "qa_growth_headwinds", "status": "aligned"},
            {"moment_id": "qa_q1_miss_explanation", "status": "aligned"},
        ]
    }
    visual_payload = {"status": "skipped"}

    panel_payload, pressure_panel, disagreement_panel = build_panel_payload(
        manifest,
        comparison_payload,
        disagreement_payload,
        audio_payload,
        visual_payload,
    )

    assert panel_payload["selected_moment_count"] == manifest["primary_moment_count"]
    assert len(pressure_panel["rows"]) == 3
    assert disagreement_panel["rows"][0]["moment_id"] == "qa_q1_miss_explanation"


def test_build_visual_support_uses_observational_only_terms(monkeypatch) -> None:
    manifest = {
        "moments": [
            {
                "moment_id": "qa_growth_headwinds",
                "audio_row_id": "audio_row_1",
            }
        ]
    }
    monkeypatch.setattr(
        netflix_panel,
        "resolve_video_source",
        lambda video_path=None: {
            "requested_path": "/tmp/requested.mp4",
            "requested_exists": False,
            "fallback_candidates": ["/tmp/fallback.mp4"],
            "resolved_video_path": "/tmp/fallback.mp4",
            "resolved_from_fallback": True,
        },
    )
    monkeypatch.setattr(
        netflix_panel,
        "_load_audio_rows",
        lambda root=None: {
            "audio_row_1": {
                "answer_start_s": 48.16,
                "answer_end_s": 196.24,
                "management_answer_excerpt": "Management answer.",
            }
        },
    )
    monkeypatch.setattr(
        netflix_panel,
        "write_visual_behavior_outputs",
        lambda video_file, qa_segments_df, visual_dir, sample_fps=0.25: {
            "frames_path": visual_dir / "visual_behavior_frames.csv",
            "segments_path": visual_dir / "visual_behavior_segments.csv",
            "summary_path": visual_dir / "visual_behavior_summary.json",
            "segments_df": pd.DataFrame(
                [
                    {
                        "segment_id": 1,
                        "start_time_s": 48.16,
                        "end_time_s": 196.24,
                        "visual_stability_label": "stable",
                        "support_direction": "supportive",
                        "support_note": "visible delivery stayed comparatively steady in this window",
                        "confidence_note": "pose coverage is limited for shoulder and hand features",
                        "face_visible_pct": 1.0,
                        "visual_change_score": 0.0601,
                        "head_motion_energy": 0.0698,
                    }
                ]
            ),
            "summary": {
                "schema_version": "1.2.0",
                "video_available": True,
                "visual_features_available": True,
                "video_quality_ok": True,
                "quality_gate": {"quality_ok": True},
                "video_metadata": {"duration_s": 2598.986},
                "face_visibility_overall": {"level": "high"},
                "prepared_baseline_visual_stability": {"level": "high"},
                "qa_visual_shift_score": {"level": "low"},
                "facial_tension_level": {"level": "low"},
                "head_motion_pressure": {"level": "low"},
                "visual_stability": {"level": "high"},
                "support_mode": "heuristic_fallback",
                "visual_confidence_support": {
                    "level": "high",
                    "suppressed": False,
                    "reason": "usable face visibility and landmark support",
                },
                "model_support": {
                    "available": False,
                    "mode": "heuristic_fallback",
                    "reason": "No usable visual segments were available for model-backed scoring.",
                },
                "strongest_visual_evidence": [
                    {
                        "segment_id": 1,
                        "section": "q_and_a",
                        "speaker_role": "management",
                        "start_time_s": 48.16,
                        "end_time_s": 196.24,
                        "visual_change_score": 0.0601,
                        "head_motion_energy": 0.0698,
                        "head_pose_drift_mean": 0.01,
                        "blink_rate_per_10s": 0.5,
                        "face_visible_pct": 1.0,
                        "confidence_note": "pose coverage is limited for shoulder and hand features",
                        "support_direction": "supportive",
                        "text": "Management answer.",
                    }
                ],
                "most_visually_changed_segments": [],
                "notable_low_confidence_segments": [],
                "limitations": [],
            },
        },
    )

    payload, skipped = build_visual_support(manifest, root=REPO_ROOT, video_path="/tmp/requested.mp4", sample_fps=0.25)

    assert skipped is False
    assert payload["status"] == "ok"
    assert payload["moments"][0]["observation_tag"] == "steady_visible_delivery"
    assert payload["moments"][0]["quality_note"] == "pose coverage is limited for shoulder and hand features"
    assert "support_direction" not in payload["moments"][0]
    assert "confidence_note" not in payload["moments"][0]
    assert payload["summary"]["quality_assessment"]["reason"] == "face visibility and landmark coverage were usable for a bounded visual pass"
    assert "visual_support_direction" not in payload["summary"]


def test_render_panel_markdown_includes_full_review_sections() -> None:
    panel_payload = {
        "panel_rows": [
            {
                "moment_id": "qa_growth_headwinds",
                "rank": 1,
                "top_8_showcase": True,
                "raw_quote_or_span": "Quote.",
                "deterministic_signal": {"category": "growth_pressure", "label": "pressure", "summary": "summary"},
                "sidecar_outputs": {
                    "consensus_label": "negative",
                    "deterministic_alignment": "mixed_vs_expected_category",
                    "pairwise_disagreement": True,
                },
                "audio_support": {"status": "aligned", "plain_english_audio_summary": "hesitant answer", "answer_time_range": "00:48-03:16"},
                "visual_support": {
                    "status": "aligned",
                    "observation_tag": "steady_visible_delivery",
                    "observation_note": "visible delivery stayed comparatively steady in this window",
                    "quality_note": "pose coverage is limited for shoulder and hand features",
                },
                "reviewer_note": "Keep transcript first.",
                "caveat": "Deterministic transcript-backed artifacts stay canonical.",
            }
        ],
        "strong_supporting_alignment_moments": [
            {"moment_id": "letter_growth_slowdown", "consensus_label": "negative", "reviewer_note": "Cleaner optional-support example."}
        ],
        "what_sidecars_added": ["A disagreement shortlist."],
        "what_sidecars_did_not_add": ["No adjudication."],
        "future_ui_surface_notes": ["Surface the top-8 showcase first."],
    }
    pressure_panel = {
        "rows": [
            {
                "moment_id": "qa_growth_headwinds",
                "analyst_question": "Question?",
                "executive_answer": "Answer.",
                "deterministic_read": "Transcript-backed read.",
                "nlp_sidecar_read": {"consensus_label": "negative"},
                "audio_support": {"status": "aligned", "plain_english_audio_summary": "hesitant answer", "answer_time_range": "00:48-03:16"},
                "visual_support": {
                    "status": "aligned",
                    "observation_tag": "steady_visible_delivery",
                    "observation_note": "visible delivery stayed comparatively steady in this window",
                    "quality_note": "pose coverage is limited for shoulder and hand features",
                },
                "reviewer_note": "Keep transcript first.",
            }
        ]
    }
    disagreement_panel = {
        "rows": [
            {
                "moment_id": "qa_growth_headwinds",
                "observed_labels": ["negative", "neutral"],
                "alignment": "mixed_vs_expected_category",
                "quote_or_span": "Quote.",
                "audio_support": {"status": "aligned", "plain_english_audio_summary": "hesitant answer", "answer_time_range": "00:48-03:16"},
                "visual_support": {
                    "status": "aligned",
                    "observation_tag": "steady_visible_delivery",
                    "observation_note": "visible delivery stayed comparatively steady in this window",
                    "quality_note": "pose coverage is limited for shoulder and hand features",
                },
            }
        ]
    }

    rendered = _render_panel_markdown(panel_payload, pressure_panel, disagreement_panel)

    assert "## Selected Moments" in rendered
    assert "- Sidecar read: consensus `negative` | alignment `mixed_vs_expected_category` | pairwise disagreement `True`" in rendered
    assert "- Visual support: steady_visible_delivery: visible delivery stayed comparatively steady in this window (quality note: pose coverage is limited for shoulder and hand features)" in rendered
    assert "## What Sidecars Added" in rendered
    assert "## Later UI Surfacing" in rendered


def test_build_netflix_multimodal_panel_script_invokes_writer(monkeypatch, capsys) -> None:
    script_path = REPO_ROOT / "scripts" / "build_netflix_multimodal_panel.py"
    spec = importlib.util.spec_from_file_location("build_netflix_multimodal_panel_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    called = {}

    def fake_write_review_bundle(*, video_path=None, models=None, device="auto", sample_fps=0.25):
        called["video_path"] = video_path
        called["models"] = models
        called["device"] = device
        called["sample_fps"] = sample_fps
        return {"bundle_paths": {"panel_json": "/tmp/netflix_multimodal_panel.json"}}

    monkeypatch.setattr(module, "write_review_bundle", fake_write_review_bundle)

    result = module.main(["--device", "cpu", "--visual-sample-fps", "0.5", "--models", "finbert_tone", "mpnet_embeddings"])

    assert result == 0
    assert called["device"] == "cpu"
    assert called["sample_fps"] == 0.5
    assert called["models"] == ["finbert_tone", "mpnet_embeddings"]
    assert "panel_json" in capsys.readouterr().out
