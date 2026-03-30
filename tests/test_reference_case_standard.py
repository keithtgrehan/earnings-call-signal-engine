from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.reference_case_standard import (
    REQUIRED_CAVEAT_IDS,
    default_supporting_only_caveats,
    validate_reference_case_package,
)


def test_default_supporting_only_caveats_covers_required_ids() -> None:
    payload = default_supporting_only_caveats("Meta Q3 2022")
    caveat_ids = {str(item["id"]) for item in payload}
    assert set(REQUIRED_CAVEAT_IDS).issubset(caveat_ids)


def test_validate_reference_case_package_accepts_minimal_valid_layout(tmp_path: Path) -> None:
    package_dir = tmp_path / "case"
    package_dir.mkdir()
    prefix = "meta"

    (package_dir / f"{prefix}_multimodal_moment_manifest.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_multimodal_panel.md").write_text("# Panel\n", encoding="utf-8")
    (package_dir / f"{prefix}_clip_manifest.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_pressure_moments_panel.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_disagreement_hotspots_panel.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_supporting_only_caveats.json").write_text(
        json.dumps(default_supporting_only_caveats("Meta Q3 2022"), indent=2),
        encoding="utf-8",
    )
    (package_dir / f"{prefix}_visual_support_skipped.json").write_text(
        json.dumps({"status": "skipped", "reason": "No usable video was available."}, indent=2),
        encoding="utf-8",
    )
    (package_dir / f"{prefix}_multimodal_panel.json").write_text(
        json.dumps(
            {
                "case_scope": "meta_q3_2022",
                "deterministic_transcript_first_is_canonical": True,
                "support_layers_are_supporting_only": True,
                "no_predictive_claims": True,
                "no_statistical_claims": True,
                "moments": [{"moment_id": "m01"}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    assert validate_reference_case_package(package_dir, prefix) == []


def test_validate_reference_case_package_flags_missing_visual_and_caveat_requirements(tmp_path: Path) -> None:
    package_dir = tmp_path / "case"
    package_dir.mkdir()
    prefix = "netflix"

    (package_dir / f"{prefix}_multimodal_moment_manifest.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_multimodal_panel.md").write_text("# Panel\n", encoding="utf-8")
    (package_dir / f"{prefix}_clip_manifest.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_supporting_only_caveats.json").write_text(
        json.dumps([{"id": "transcript_first_canonical", "message": "ok"}], indent=2),
        encoding="utf-8",
    )
    (package_dir / f"{prefix}_multimodal_panel.json").write_text(
        json.dumps({"case_scope": "netflix_q1_2022", "moments": []}, indent=2),
        encoding="utf-8",
    )

    errors = validate_reference_case_package(package_dir, prefix)

    assert any("missing visual status artifact" in error for error in errors)
    assert any("supporting-only caveats missing `support_layers_supporting_only`" in error for error in errors)
    assert any("panel json must include at least one moment row" in error for error in errors)


def test_validate_reference_case_package_accepts_legacy_netflix_style_layout(tmp_path: Path) -> None:
    package_dir = tmp_path / "case"
    package_dir.mkdir()
    prefix = "netflix"

    (package_dir / f"{prefix}_multimodal_moment_manifest.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_multimodal_panel.md").write_text("# Panel\n", encoding="utf-8")
    (package_dir / f"{prefix}_clip_manifest.json").write_text("[]", encoding="utf-8")
    (package_dir / f"{prefix}_supporting_only_caveats.json").write_text(
        json.dumps(
            {
                "deterministic": [
                    "Transcript-backed deterministic artifacts remain the canonical review path for this case."
                ],
                "nlp_sidecars": [
                    "Optional NLP sidecars are supporting inspection aids only."
                ],
                "audio": [
                    "Audio behavior remains supporting-only reviewer context."
                ],
                "visual": [
                    "Visual behavior is observational only and heuristic fallback should be suppressed when weak."
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (package_dir / f"{prefix}_visual_support.json").write_text(
        json.dumps({"status": "ok", "moments": []}, indent=2),
        encoding="utf-8",
    )
    (package_dir / f"{prefix}_multimodal_panel.json").write_text(
        json.dumps(
            {
                "case_id": "netflix_q1_2022",
                "status": "ok",
                "panel_rows": [{"moment_id": "m01", "caveat": "supporting-only"}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    assert validate_reference_case_package(package_dir, prefix) == []
