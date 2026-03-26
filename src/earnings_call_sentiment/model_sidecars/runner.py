"""Orchestration helpers for optional model-sidecar benchmark runs."""

from __future__ import annotations

import math
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from .config import load_zero_shot_label_groups
from .io import (
    build_case_sidecar_output_dir,
    load_prior_guidance_pairs,
    load_units_for_case,
    resolve_case_artifacts,
    write_classification_outputs,
    write_embedding_outputs,
)
from .models.base import BaseClassificationSidecar, BaseEmbeddingSidecar, EmbeddingOutput
from .models.registry import build_model


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    denominator = float(np.linalg.norm(left_array) * np.linalg.norm(right_array))
    if math.isclose(denominator, 0.0):
        return 0.0
    return float(np.dot(left_array, right_array) / denominator)


def _within_case_similarity(
    unit_type: str,
    rows: list[EmbeddingOutput],
    *,
    top_k: int = 3,
) -> dict[str, Any]:
    neighbors: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        ranked: list[dict[str, Any]] = []
        for other_index, other_row in enumerate(rows):
            if index == other_index:
                continue
            ranked.append(
                {
                    "source_id": other_row.unit.source_id,
                    "section": other_row.unit.section,
                    "speaker": other_row.unit.speaker,
                    "similarity": round(_cosine_similarity(row.vector, other_row.vector), 6),
                    "text": other_row.unit.text[:220],
                }
            )
        ranked.sort(key=lambda item: float(item["similarity"]), reverse=True)
        neighbors.append(
            {
                "source_id": row.unit.source_id,
                "section": row.unit.section,
                "speaker": row.unit.speaker,
                "text": row.unit.text[:220],
                "nearest_neighbors": ranked[:top_k],
            }
        )
    return {
        "mode": "within_case",
        "unit_type": unit_type,
        "neighbors": neighbors[: min(len(neighbors), 25)],
    }


def _prior_guidance_similarity(
    *,
    model: BaseEmbeddingSidecar,
    case_pairs: list[dict[str, Any]],
    batch_size: int,
) -> dict[str, Any]:
    current_vectors = model.encode_texts(
        [pair["current_text"] for pair in case_pairs],
        batch_size=batch_size,
    )
    prior_vectors = model.encode_texts(
        [pair["prior_text"] for pair in case_pairs],
        batch_size=batch_size,
    )
    rows: list[dict[str, Any]] = []
    for pair, current_vector, prior_vector in zip(
        case_pairs,
        current_vectors,
        prior_vectors,
        strict=True,
    ):
        rows.append(
            {
                **pair,
                "similarity": round(_cosine_similarity(current_vector, prior_vector), 6),
            }
        )
    rows.sort(key=lambda item: float(item["similarity"]), reverse=True)
    return {
        "mode": "prior_guidance_comparison",
        "unit_type": "guidance_spans",
        "pairs": rows,
    }


def run_model_sidecars(
    *,
    case_ids: list[str],
    model_names: list[str],
    unit_types: list[str],
    output_dir: str | Path | None = None,
    zero_shot_label_config: str | Path | None = None,
    batch_size: int = 8,
    max_length: int = 512,
    device: str = "auto",
    case_dir: str | Path | None = None,
) -> dict[str, Any]:
    label_groups: dict[str, list[str]] | None = None
    if "deberta_zero_shot" in model_names:
        label_groups = load_zero_shot_label_groups(zero_shot_label_config)

    report: dict[str, Any] = {"cases": []}
    for case_id in case_ids:
        case = resolve_case_artifacts(case_id, case_dir=case_dir)
        units_by_type = load_units_for_case(case, unit_types=unit_types)
        case_output_root = build_case_sidecar_output_dir(case_id, output_dir=output_dir)
        case_output_root.mkdir(parents=True, exist_ok=True)

        case_summary: dict[str, Any] = {
            "case_id": case_id,
            "input_root": str(case.input_root),
            "output_root": str(case_output_root),
            "models": {},
        }

        for model_name in model_names:
            model = build_model(model_name, device=device)
            started = perf_counter()
            if isinstance(model, BaseEmbeddingSidecar):
                outputs_by_unit: dict[str, list[EmbeddingOutput]] = {}
                similarity_by_unit: dict[str, dict[str, Any]] = {}
                for unit_type in unit_types:
                    rows = model.embed(units_by_type[unit_type], batch_size=batch_size)
                    outputs_by_unit[unit_type] = rows
                    if unit_type == "guidance_spans":
                        prior_pairs = load_prior_guidance_pairs(case)
                        if prior_pairs:
                            similarity_by_unit[unit_type] = _prior_guidance_similarity(
                                model=model,
                                case_pairs=prior_pairs,
                                batch_size=batch_size,
                            )
                        else:
                            similarity_by_unit[unit_type] = _within_case_similarity(
                                unit_type,
                                rows,
                            )
                    else:
                        similarity_by_unit[unit_type] = _within_case_similarity(unit_type, rows)
                runtime_s = perf_counter() - started
                artifacts = write_embedding_outputs(
                    case_id=case_id,
                    model_name=model_name,
                    model_id=model.model_id,
                    output_root=case_output_root,
                    outputs_by_unit=outputs_by_unit,
                    similarity_by_unit=similarity_by_unit,
                    runtime_s=runtime_s,
                )
            elif isinstance(model, BaseClassificationSidecar):
                outputs_by_unit = {}
                for unit_type in unit_types:
                    outputs_by_unit[unit_type] = model.predict(
                        units_by_type[unit_type],
                        batch_size=batch_size,
                        max_length=max_length,
                        label_groups=label_groups,
                    )
                runtime_s = perf_counter() - started
                artifacts = write_classification_outputs(
                    case_id=case_id,
                    model_name=model_name,
                    model_id=model.model_id,
                    output_root=case_output_root,
                    outputs_by_unit=outputs_by_unit,
                    runtime_s=runtime_s,
                )
            else:  # pragma: no cover - registry only returns supported subclasses
                raise RuntimeError(f"Unsupported model-sidecar class for '{model_name}'.")

            case_summary["models"][model_name] = {
                "runtime_s": round(runtime_s, 4),
                "artifacts": {key: str(value) for key, value in artifacts.items()},
            }

        report["cases"].append(case_summary)
    return report
