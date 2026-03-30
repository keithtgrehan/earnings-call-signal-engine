from __future__ import annotations

import importlib.util
from pathlib import Path

import earnings_call_sentiment.netflix_multimodal_panel as netflix_panel
from earnings_call_sentiment.netflix_multimodal_panel import (
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
