from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_CAVEAT_IDS = (
    "transcript_first_canonical",
    "support_layers_supporting_only",
    "weak_or_missing_support_explicit",
    "heuristic_visual_context_only",
    "no_predictive_claims",
    "no_statistical_claims",
)

LEGACY_REQUIRED_CAVEAT_GROUPS = (
    "deterministic",
    "audio",
    "visual",
)


def expected_reference_case_paths(package_dir: Path, prefix: str) -> dict[str, Path]:
    return {
        "moment_manifest": package_dir / f"{prefix}_multimodal_moment_manifest.json",
        "panel_json": package_dir / f"{prefix}_multimodal_panel.json",
        "panel_markdown": package_dir / f"{prefix}_multimodal_panel.md",
        "clip_manifest": package_dir / f"{prefix}_clip_manifest.json",
        "caveats_json": package_dir / f"{prefix}_supporting_only_caveats.json",
        "pressure_panel": package_dir / f"{prefix}_pressure_moments_panel.json",
        "disagreement_panel": package_dir / f"{prefix}_disagreement_hotspots_panel.json",
        "visual_support": package_dir / f"{prefix}_visual_support.json",
        "visual_skip": package_dir / f"{prefix}_visual_support_skipped.json",
    }


def default_supporting_only_caveats(case_scope: str) -> list[dict[str, str]]:
    scope_text = str(case_scope).strip() or "this case"
    return [
        {
            "id": "transcript_first_canonical",
            "message": f"Deterministic transcript-backed outputs remain the canonical review layer for {scope_text}.",
        },
        {
            "id": "support_layers_supporting_only",
            "message": "Audio, NLP, and visual layers are supporting-only reviewer context and do not override transcript-backed outputs.",
        },
        {
            "id": "weak_or_missing_support_explicit",
            "message": "Missing, weak, or suppressed support layers must stay explicit rather than being normalized into a stronger read.",
        },
        {
            "id": "heuristic_visual_context_only",
            "message": "Heuristic visual output is context only and must not be presented as corroboration or proof.",
        },
        {
            "id": "no_predictive_claims",
            "message": "The package does not make predictive-edge, return, or trading-value claims.",
        },
        {
            "id": "no_statistical_claims",
            "message": "The package does not make statistical-significance claims.",
        },
    ]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_caveat_ids(payload: Any) -> set[str]:
    if isinstance(payload, list):
        return {
            str(item.get("id", "")).strip()
            for item in payload
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        }
    if isinstance(payload, dict):
        return {
            str(key).strip()
            for key in payload.keys()
            if str(key).strip()
        }
    return set()


def _collect_text_strings(payload: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(payload, str):
        text = payload.strip()
        if text:
            strings.append(text)
        return strings
    if isinstance(payload, dict):
        for value in payload.values():
            strings.extend(_collect_text_strings(value))
        return strings
    if isinstance(payload, list):
        for item in payload:
            strings.extend(_collect_text_strings(item))
    return strings


def _has_phrase(payload: Any, *needles: str) -> bool:
    haystack = " ".join(_collect_text_strings(payload)).lower()
    return all(needle.lower() in haystack for needle in needles)


def _validate_panel_payload(payload: Any, panel_path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"panel json must be an object: {panel_path}"]

    if "case_scope" not in payload and "case_id" not in payload:
        errors.append(f"panel json missing case identifier (`case_scope` or `case_id`): {panel_path}")

    moments = payload.get("moments")
    if moments is None:
        moments = payload.get("panel_rows")
    if not isinstance(moments, list) or not moments:
        errors.append(f"panel json must include at least one moment row under `moments` or `panel_rows`: {panel_path}")

    if "moments" in payload:
        for key in (
            "deterministic_transcript_first_is_canonical",
            "support_layers_are_supporting_only",
            "no_predictive_claims",
            "no_statistical_claims",
        ):
            if key not in payload:
                errors.append(f"panel json missing required key `{key}`: {panel_path}")

    return errors


def _validate_caveat_payload(payload: Any, caveat_path: Path) -> list[str]:
    errors: list[str] = []
    if isinstance(payload, list):
        caveat_ids = _collect_caveat_ids(payload)
        for caveat_id in REQUIRED_CAVEAT_IDS:
            if caveat_id not in caveat_ids:
                errors.append(f"supporting-only caveats missing `{caveat_id}`: {caveat_path}")
        return errors

    if isinstance(payload, dict):
        keys = {str(key).strip() for key in payload.keys() if str(key).strip()}
        if set(LEGACY_REQUIRED_CAVEAT_GROUPS).issubset(keys):
            if not _has_phrase(payload.get("deterministic", []), "transcript", "canonical"):
                errors.append(
                    f"legacy deterministic caveats must state that transcript-backed artifacts remain canonical: {caveat_path}"
                )
            if not _has_phrase(payload, "supporting"):
                errors.append(f"legacy caveats must describe support layers as supporting-only or inspection-only: {caveat_path}")
            if not (
                _has_phrase(payload.get("visual", []), "heuristic")
                or _has_phrase(payload.get("visual", []), "suppressed")
                or _has_phrase(payload.get("visual", []), "observational")
            ):
                errors.append(
                    f"legacy visual caveats must describe heuristic or observational limits explicitly: {caveat_path}"
                )
            return errors

        caveat_ids = _collect_caveat_ids(payload)
        for caveat_id in REQUIRED_CAVEAT_IDS:
            if caveat_id not in caveat_ids:
                errors.append(f"supporting-only caveats missing `{caveat_id}`: {caveat_path}")
        return errors

    errors.append(f"supporting-only caveats must be a list or object: {caveat_path}")
    return errors


def validate_reference_case_package(package_dir: Path, prefix: str) -> list[str]:
    errors: list[str] = []
    paths = expected_reference_case_paths(package_dir, prefix)

    for key in ("moment_manifest", "panel_json", "panel_markdown", "clip_manifest", "caveats_json"):
        if not paths[key].exists():
            errors.append(f"missing required artifact: {paths[key]}")

    if not (paths["visual_support"].exists() or paths["visual_skip"].exists()):
        errors.append(
            "missing visual status artifact: expected either "
            f"{paths['visual_support'].name} or {paths['visual_skip'].name}"
        )

    if paths["panel_json"].exists():
        errors.extend(_validate_panel_payload(_read_json(paths["panel_json"]), paths["panel_json"]))

    if paths["caveats_json"].exists():
        errors.extend(_validate_caveat_payload(_read_json(paths["caveats_json"]), paths["caveats_json"]))

    if paths["visual_skip"].exists():
        payload = _read_json(paths["visual_skip"])
        if not isinstance(payload, dict):
            errors.append(f"visual skip payload must be an object: {paths['visual_skip']}")
        else:
            status = str(payload.get("status", "")).strip().lower()
            reason = str(payload.get("reason", "")).strip()
            if status != "skipped":
                errors.append(f"visual skip payload must set status=skipped: {paths['visual_skip']}")
            if not reason:
                errors.append(f"visual skip payload must include a non-empty reason: {paths['visual_skip']}")

    return errors
