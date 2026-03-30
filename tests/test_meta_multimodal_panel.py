from __future__ import annotations

import importlib.util
from pathlib import Path

import earnings_call_sentiment.meta_multimodal_panel as meta_panel
from earnings_call_sentiment.meta_multimodal_panel import (
    CASE_SCOPE,
    _visual_moment_row,
    build_audio_support,
    build_curated_moment_manifest,
    build_model_comparison,
    build_panel_payload,
    write_curated_sidecar_inputs,
)
from earnings_call_sentiment.reference_case_standard import REQUIRED_CAVEAT_IDS, default_supporting_only_caveats


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_curated_moment_manifest_has_expected_showcase_shape() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)

    assert manifest["case_id"] == "meta_q3_2022"
    assert 8 <= manifest["primary_moment_count"] <= 20
    assert manifest["showcase_moment_count"] == 8
    moment_ids = [row["moment_id"] for row in manifest["moments"]]
    assert "transcript_macro_ads_pressure" in moment_ids
    assert "qa_reels_transition_pressure" in moment_ids
    assert moment_ids[:2] == ["transcript_macro_ads_pressure", "transcript_conservative_budget"]


def test_write_curated_sidecar_inputs_preserves_manifest_ids(tmp_path: Path) -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    paths = write_curated_sidecar_inputs(manifest, output_dir=tmp_path)

    chunks_text = paths["chunks"].read_text(encoding="utf-8")
    guidance_text = paths["guidance_spans"].read_text(encoding="utf-8")
    qa_text = paths["qa_answers"].read_text(encoding="utf-8")

    assert "transcript_macro_ads_pressure" in chunks_text
    assert "guidance_q4_revenue_outlook" in guidance_text
    assert "qa_capex_ai_pressure" in qa_text


def test_build_audio_support_marks_only_curated_audio_rows_as_aligned() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    payload = build_audio_support(manifest, root=REPO_ROOT)

    aligned = [row for row in payload["moments"] if row["status"] == "aligned"]
    unavailable = [row for row in payload["moments"] if row["status"] == "unavailable"]

    assert payload["audio_available"] is True
    assert len(aligned) == 2
    assert len(unavailable) >= 1


def test_build_audio_support_interpretation_stays_supporting_only() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    payload = build_audio_support(manifest, root=REPO_ROOT)

    aligned = [row for row in payload["moments"] if row["status"] == "aligned"]

    assert aligned
    assert all("pacing/context only" in str(row["plain_english_interpretation"]) for row in aligned)
    assert all("does not change the transcript-first deterministic read" in str(row["plain_english_interpretation"]) for row in aligned)


def test_build_visual_support_skips_cleanly_when_video_missing(monkeypatch) -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    monkeypatch.setattr(meta_panel, "REQUESTED_VIDEO_PATH", Path("/tmp/meta-video-missing-requested.mp4"))
    monkeypatch.setattr(meta_panel, "FALLBACK_VIDEO_PATH", Path("/tmp/meta-video-missing-fallback.mp4"))
    payload, skipped = meta_panel.build_visual_support(
        manifest,
        root=REPO_ROOT,
        video_path="/tmp/meta-video-missing.mp4",
        sample_fps=0.25,
    )

    assert skipped is True
    assert payload["status"] == "skipped"


def test_build_visual_support_can_skip_when_runtime_budget_is_bounded() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    payload, skipped = meta_panel.build_visual_support(
        manifest,
        root=REPO_ROOT,
        sample_fps=0.0,
    )

    assert skipped is True
    assert payload["status"] == "skipped"
    assert "runtime cap" in payload["reason"]


def test_visual_moment_row_softens_heuristic_fallback_language() -> None:
    softened = _visual_moment_row(
        {
            "start_time_s": 1.0,
            "end_time_s": 2.0,
            "visual_stability_label": "stable",
            "support_direction": "supportive",
            "support_note": "visible delivery stayed comparatively steady in this window",
            "confidence_note": "usable visual segment",
            "face_visible_pct": 1.0,
            "visual_change_score": 0.05,
            "head_motion_energy": 0.06,
        },
        support_mode="heuristic_fallback",
    )

    assert softened["status"] == "aligned"
    assert softened["context_role"] == "context_only"
    assert "heuristic fallback only" in softened["context_note"]
    assert "heuristic fallback only" in softened["quality_note"]


def test_build_model_comparison_has_expected_shape_without_sidecar_outputs() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    comparison_payload, disagreement_payload = build_model_comparison(manifest, root=REPO_ROOT)

    assert comparison_payload["status"] in {"ok", "no_sidecar_outputs"}
    assert len(comparison_payload["moment_rows"]) == manifest["primary_moment_count"]
    assert "pairwise_model_disagreements" in disagreement_payload


def test_build_panel_payload_returns_pressure_rows() -> None:
    manifest = build_curated_moment_manifest(REPO_ROOT)
    comparison_payload = {
        "moment_rows": [
            {
                "moment_id": "qa_capex_ai_pressure",
                "leading_sidecar_label": "negative",
                "pairwise_disagreement": False,
                "expected_direction_check": "all_comparable_labels_match_expected_direction",
                "review_bucket": "consistent_directional_read",
                "review_priority_reason": "Comparable sidecar labels point in the same direction as the expected deterministic read.",
            },
            {
                "moment_id": "qa_reels_transition_pressure",
                "leading_sidecar_label": "negative",
                "pairwise_disagreement": True,
                "expected_direction_check": "some_comparable_labels_match_expected_direction",
                "review_bucket": "directional_conflict",
                "review_priority_reason": "Comparable sidecar labels split across positive and negative directions on a moment with an expected deterministic polarity.",
            },
        ]
    }
    disagreement_payload = {
        "pairwise_model_disagreements": [
            {
                "moment_id": "qa_reels_transition_pressure",
                "quote_or_span": "A disagreement hotspot.",
                "expected_direction_check": "some_comparable_labels_match_expected_direction",
                "review_bucket": "directional_conflict",
                "review_priority": "high",
                "review_priority_reason": "Needs transcript-first review.",
            }
        ]
    }
    audio_payload = {
        "moments": [
            {"moment_id": "qa_capex_ai_pressure", "status": "aligned"},
            {"moment_id": "qa_reels_transition_pressure", "status": "aligned"},
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
    assert "strong_supporting_context_moments" in panel_payload
    assert len(pressure_panel["rows"]) >= 4
    assert disagreement_panel["rows"][0]["moment_id"] == "qa_reels_transition_pressure"


def test_default_meta_caveats_cover_required_ids() -> None:
    caveat_ids = {str(item["id"]) for item in default_supporting_only_caveats(CASE_SCOPE)}
    assert set(REQUIRED_CAVEAT_IDS).issubset(caveat_ids)


def test_build_meta_multimodal_panel_script_invokes_writer(monkeypatch, capsys) -> None:
    script_path = REPO_ROOT / "scripts" / "build_meta_multimodal_panel.py"
    spec = importlib.util.spec_from_file_location("build_meta_multimodal_panel_script", script_path)
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
        return {"bundle_paths": {"panel_json": "/tmp/meta_multimodal_panel.json"}}

    monkeypatch.setattr(module, "write_review_bundle", fake_write_review_bundle)

    result = module.main(["--device", "cpu", "--visual-sample-fps", "0.5", "--models", "finbert_tone", "mpnet_embeddings"])

    assert result == 0
    assert called["device"] == "cpu"
    assert called["sample_fps"] == 0.5
    assert called["models"] == ["finbert_tone", "mpnet_embeddings"]
    assert "panel_json" in capsys.readouterr().out
