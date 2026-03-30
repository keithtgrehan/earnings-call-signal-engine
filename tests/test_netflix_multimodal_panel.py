from __future__ import annotations

import importlib.util
from pathlib import Path

import earnings_call_sentiment.netflix_multimodal_panel as netflix_panel
from earnings_call_sentiment.netflix_multimodal_panel import (
    build_model_comparison,
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


def test_build_curated_moment_manifest_showcase_rows_have_reviewer_rationale() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)

    showcase_rows = [row for row in manifest["moments"] if row["top_8_showcase"]]

    assert len(showcase_rows) == 8
    assert all(str(row["why_selected"]).strip() for row in showcase_rows)
    guidance_row = next(row for row in showcase_rows if row["moment_id"] == "guidance_negative_q2_net_adds")
    assert "guide reset language" in guidance_row["why_selected"]


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


def test_build_audio_support_interpretation_stays_observational() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    payload = build_audio_support(manifest, root=REPO_ROOT)

    aligned = [row for row in payload["moments"] if row["status"] == "aligned"]

    assert aligned
    assert all("pacing/context only" in str(row["plain_english_interpretation"]) for row in aligned)
    assert all("does not change the transcript-backed deterministic read" in str(row["plain_english_interpretation"]) for row in aligned)


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


def test_visual_moment_row_softens_heuristic_fallback_language() -> None:
    softened = netflix_panel._visual_moment_row(
        {
            "start_time_s": 1.0,
            "end_time_s": 2.0,
            "visual_stability_label": "stable",
            "support_direction": "supportive",
            "support_note": "visible delivery stayed comparatively steady in this window",
            "confidence_note": "pose coverage is limited",
            "face_visible_pct": 1.0,
            "visual_change_score": 0.05,
            "head_motion_energy": 0.06,
        },
        support_mode="heuristic_fallback",
    )

    assert softened["support_direction"] == "context_only"
    assert "heuristic fallback only" in softened["support_note"]
    assert "heuristic fallback only" in softened["confidence_note"]


def test_support_signal_metadata_downgrades_non_polar_spread() -> None:
    metadata = netflix_panel._support_signal_metadata(
        expected_polarity="",
        comparable_labels=["positive", "neutral", "neutral"],
        consensus_label="neutral",
    )

    assert metadata["support_signal_bucket"] == "non_polar_context_only"
    assert metadata["review_priority"] == "low"


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


def test_build_model_comparison_adds_review_priority_metadata() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    comparison_payload, disagreement_payload = build_model_comparison(manifest, root=REPO_ROOT)

    rows = {row["moment_id"]: row for row in comparison_payload["moment_rows"]}
    priorities = {"high": 0, "medium": 1, "low": 2}

    assert rows["qa_ad_supported_option"]["support_signal_bucket"] == "non_polar_context_only"
    assert rows["qa_ad_supported_option"]["review_priority"] == "low"
    assert rows["chunk_long_term_market_unchanged"]["review_priority"] == "high"
    assert all("review_priority_reason" in row for row in disagreement_payload["pairwise_model_disagreements"])
    priority_values = [priorities[row["review_priority"]] for row in disagreement_payload["pairwise_model_disagreements"]]
    assert priority_values == sorted(priority_values)


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
