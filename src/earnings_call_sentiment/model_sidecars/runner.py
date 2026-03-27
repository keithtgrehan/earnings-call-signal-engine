"""Orchestration helpers for optional model-sidecar benchmark runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path
import random
import sys
from time import perf_counter
from typing import Any

import numpy as np

from .config import load_zero_shot_label_groups
from .io import (
    build_case_sidecar_output_dir,
    completion_rule_for,
    expected_unit_artifact_paths,
    load_prior_guidance_pairs,
    load_units_for_case,
    resolve_case_artifacts,
    unit_output_complete,
    write_classification_unit_output,
    write_embedding_unit_output,
    write_model_run_summary,
)
from .models.base import BaseClassificationSidecar, BaseEmbeddingSidecar, EmbeddingOutput, TextUnit
from .models.registry import build_model

SUPPORTED_SAMPLE_STRATEGIES = ("head", "random", "stratified")
ZERO_SHOT_MODEL_NAMES = {"deberta_zero_shot", "distilbart_zero_shot_smoke"}


@dataclass(frozen=True)
class SamplingConfig:
    limit: int | None = None
    sample_size: int | None = None
    sample_strategy: str = "head"
    seed: int = 7


def _validate_sampling_config(config: SamplingConfig) -> None:
    if config.limit is not None and config.limit <= 0:
        raise RuntimeError("--limit must be a positive integer when provided.")
    if config.sample_size is not None and config.sample_size <= 0:
        raise RuntimeError("--sample-size must be a positive integer when provided.")
    if config.sample_strategy not in SUPPORTED_SAMPLE_STRATEGIES:
        supported = ", ".join(SUPPORTED_SAMPLE_STRATEGIES)
        raise RuntimeError(
            f"Unsupported sample strategy '{config.sample_strategy}'. Supported values: {supported}."
        )


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


def _peak_rss_bytes() -> tuple[int | None, str]:
    try:
        import resource
    except ImportError:  # pragma: no cover - resource is available on Unix CI
        return None, "unavailable"

    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return int(usage), "resource.ru_maxrss(bytes)"
    return int(usage) * 1024, "resource.ru_maxrss(kib)"


def _sampling_group_key(unit: TextUnit) -> str:
    return str(unit.section or unit.speaker or unit.unit_type or "unknown")


def _round_robin_stratified_sample(
    units: list[TextUnit],
    *,
    sample_size: int,
    seed: int,
) -> list[TextUnit]:
    groups: dict[str, list[TextUnit]] = {}
    for unit in units:
        groups.setdefault(_sampling_group_key(unit), []).append(unit)

    rng = random.Random(seed)
    for group in groups.values():
        rng.shuffle(group)
    ordered_group_names = sorted(groups)
    selected: list[TextUnit] = []
    cursor = 0
    while len(selected) < sample_size and ordered_group_names:
        group_name = ordered_group_names[cursor % len(ordered_group_names)]
        group = groups[group_name]
        if group:
            selected.append(group.pop(0))
        if not group:
            ordered_group_names = [name for name in ordered_group_names if groups[name]]
            cursor = 0
            continue
        cursor += 1
    return selected


def _apply_sampling(
    units: list[TextUnit],
    *,
    config: SamplingConfig,
) -> tuple[list[TextUnit], dict[str, Any]]:
    _validate_sampling_config(config)
    available_units = list(units)
    limited_units = (
        available_units[: config.limit]
        if config.limit is not None
        else list(available_units)
    )

    selected_units = list(limited_units)
    if config.sample_size is not None and config.sample_size < len(limited_units):
        if config.sample_strategy == "head":
            selected_units = limited_units[: config.sample_size]
        elif config.sample_strategy == "random":
            rng = random.Random(config.seed)
            indices = sorted(rng.sample(range(len(limited_units)), config.sample_size))
            selected_units = [limited_units[index] for index in indices]
        else:
            selected_units = _round_robin_stratified_sample(
                limited_units,
                sample_size=config.sample_size,
                seed=config.seed,
            )

    metadata = {
        "available_count": len(available_units),
        "limited_count": len(limited_units),
        "selected_count": len(selected_units),
        "limit": config.limit,
        "sample_size": config.sample_size,
        "sample_strategy": config.sample_strategy,
        "seed": config.seed,
        "sampled": len(selected_units) != len(available_units),
    }
    return selected_units, metadata


def _resolve_label_groups(
    model_names: list[str],
    zero_shot_label_config: str | Path | None,
) -> dict[str, list[str]] | None:
    if not any(model_name in ZERO_SHOT_MODEL_NAMES for model_name in model_names):
        return None
    return load_zero_shot_label_groups(zero_shot_label_config)


def prewarm_model_sidecars(
    *,
    model_names: list[str],
    device: str = "auto",
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for model_name in model_names:
        started = perf_counter()
        try:
            model = build_model(model_name, device=device)
            details = model.prewarm()
            results.append(
                {
                    **details,
                    "status": "warmed",
                    "wall_clock_s": round(perf_counter() - started, 4),
                }
            )
        except RuntimeError as exc:
            results.append(
                {
                    "model_name": model_name,
                    "status": "failed",
                    "error": str(exc),
                    "wall_clock_s": round(perf_counter() - started, 4),
                }
            )

    return {
        "requested_models": model_names,
        "device_request": device,
        "warmed_models": [
            item["model_name"] for item in results if item.get("status") == "warmed"
        ],
        "failed_models": [
            item["model_name"] for item in results if item.get("status") == "failed"
        ],
        "results": results,
    }


def _embedding_similarity_payload(
    *,
    case,
    model: BaseEmbeddingSidecar,
    unit_type: str,
    rows: list[EmbeddingOutput],
    batch_size: int,
) -> dict[str, Any]:
    if unit_type == "guidance_spans":
        prior_pairs = load_prior_guidance_pairs(case)
        if prior_pairs:
            return _prior_guidance_similarity(
                model=model,
                case_pairs=prior_pairs,
                batch_size=batch_size,
            )
    return _within_case_similarity(unit_type, rows)


def _run_single_model_for_case(
    *,
    case,
    case_output_root: Path,
    model_name: str,
    model,
    units_by_type: dict[str, list[TextUnit]],
    sampling_metadata: dict[str, dict[str, Any]],
    label_groups: dict[str, list[str]] | None,
    batch_size: int,
    max_length: int,
    resume: bool,
    force: bool,
    prewarm_models: bool,
    run_label: str | None,
) -> dict[str, Any]:
    resolved_device = str(model.device)
    prewarm_details: dict[str, Any] = {}
    prewarm_runtime_s = 0.0
    if prewarm_models:
        prewarm_started = perf_counter()
        prewarm_details = model.prewarm()
        prewarm_runtime_s = perf_counter() - prewarm_started
        resolved_device = str(prewarm_details.get("device", resolved_device))

    model_started = perf_counter()
    artifacts: dict[str, str] = {}
    unit_results: dict[str, Any] = {}
    label_distributions: dict[str, dict[str, int]] = {}
    vector_dimensions: dict[str, int] = {}
    completed_unit_runtime_s = 0.0
    memory_method = _peak_rss_bytes()[1]

    for unit_type, units in units_by_type.items():
        expected_artifacts = expected_unit_artifact_paths(
            output_root=case_output_root,
            model_name=model_name,
            unit_type=unit_type,
            output_kind=model.output_kind,
        )
        if resume and not force and unit_output_complete(
            output_root=case_output_root,
            model_name=model_name,
            unit_type=unit_type,
            output_kind=model.output_kind,
        ):
            output_path = expected_artifacts["output"]
            similarity_path = expected_artifacts.get("similarity")
            unit_results[unit_type] = {
                "status": "skipped_existing",
                "item_count": len(units),
                "available_count": sampling_metadata[unit_type]["available_count"],
                "selected_count": sampling_metadata[unit_type]["selected_count"],
                "runtime_s": 0.0,
                "items_per_s": None,
                "device": resolved_device,
                "batch_size": batch_size,
                "max_length": max_length if model.output_kind == "classification" else None,
                "output_path": str(output_path),
                "similarity_path": str(similarity_path) if similarity_path else None,
                "process_peak_rss_bytes": _peak_rss_bytes()[0],
                "process_peak_rss_delta_bytes": 0,
                "memory_measurement": memory_method,
                "warm_start": prewarm_models,
                "completion_rule": completion_rule_for(model.output_kind),
            }
            artifacts[f"{unit_type}_output"] = str(output_path)
            if similarity_path is not None:
                artifacts[f"{unit_type}_similarity"] = str(similarity_path)
            continue

        peak_before, memory_method = _peak_rss_bytes()
        unit_started = perf_counter()
        if isinstance(model, BaseEmbeddingSidecar):
            rows = model.embed(units, batch_size=batch_size)
            similarity_payload = _embedding_similarity_payload(
                case=case,
                model=model,
                unit_type=unit_type,
                rows=rows,
                batch_size=batch_size,
            )
            write_result = write_embedding_unit_output(
                case_id=case.case_id,
                model_name=model_name,
                model_id=model.model_id,
                output_root=case_output_root,
                unit_type=unit_type,
                rows=rows,
                similarity_payload=similarity_payload,
            )
            vector_dimensions[unit_type] = int(write_result["vector_dimension"])
        elif isinstance(model, BaseClassificationSidecar):
            rows = model.predict(
                units,
                batch_size=batch_size,
                max_length=max_length,
                label_groups=label_groups,
            )
            write_result = write_classification_unit_output(
                case_id=case.case_id,
                model_name=model_name,
                model_id=model.model_id,
                output_root=case_output_root,
                unit_type=unit_type,
                rows=rows,
            )
            label_distributions[unit_type] = write_result["label_distribution"]
        else:  # pragma: no cover - registry only returns supported subclasses
            raise RuntimeError(f"Unsupported model-sidecar class for '{model_name}'.")

        unit_runtime_s = perf_counter() - unit_started
        completed_unit_runtime_s += unit_runtime_s
        peak_after, memory_method = _peak_rss_bytes()
        peak_delta = (
            max(int(peak_after) - int(peak_before), 0)
            if peak_before is not None and peak_after is not None
            else None
        )

        output_path = str(write_result["path"])
        similarity_path = write_result.get("similarity_path")
        unit_results[unit_type] = {
            "status": "completed",
            "item_count": len(units),
            "available_count": sampling_metadata[unit_type]["available_count"],
            "selected_count": sampling_metadata[unit_type]["selected_count"],
            "runtime_s": round(unit_runtime_s, 4),
            "items_per_s": round(len(units) / unit_runtime_s, 4) if unit_runtime_s > 0 else None,
            "device": resolved_device,
            "batch_size": batch_size,
            "max_length": max_length if model.output_kind == "classification" else None,
            "output_path": output_path,
            "similarity_path": str(similarity_path) if similarity_path is not None else None,
            "process_peak_rss_bytes": peak_after,
            "process_peak_rss_delta_bytes": peak_delta,
            "memory_measurement": memory_method,
            "warm_start": prewarm_models,
            "completion_rule": write_result["completion_rule"],
        }
        artifacts[f"{unit_type}_output"] = output_path
        if similarity_path is not None:
            artifacts[f"{unit_type}_similarity"] = str(similarity_path)

    runtime_s = perf_counter() - model_started
    summary_payload = {
        "case_id": case.case_id,
        "model_name": model_name,
        "model_id": model.model_id,
        "output_kind": model.output_kind,
        "runtime_s": round(runtime_s, 4),
        "prewarm_runtime_s": round(prewarm_runtime_s, 4),
        "inference_runtime_s": round(completed_unit_runtime_s, 4),
        "requested_device": str(model.device),
        "device": resolved_device,
        "batch_size": batch_size,
        "max_length": max_length if model.output_kind == "classification" else None,
        "resume_enabled": resume,
        "force_recompute": force,
        "run_label": run_label,
        "unit_counts": {
            unit_type: unit_result["selected_count"]
            for unit_type, unit_result in unit_results.items()
        },
        "available_unit_counts": {
            unit_type: unit_result["available_count"]
            for unit_type, unit_result in unit_results.items()
        },
        "sampling": sampling_metadata,
        "unit_results": unit_results,
        "label_distributions": label_distributions,
        "vector_dimensions": vector_dimensions,
        "completion_rules": {
            unit_type: completion_rule_for(model.output_kind) for unit_type in units_by_type
        },
        "memory_measurement": memory_method,
        "prewarm": prewarm_details,
    }
    summary_path = write_model_run_summary(
        output_root=case_output_root,
        model_name=model_name,
        payload=summary_payload,
    )
    artifacts["run_summary"] = str(summary_path)

    return {
        "model_id": model.model_id,
        "output_kind": model.output_kind,
        "runtime_s": round(runtime_s, 4),
        "prewarm_runtime_s": round(prewarm_runtime_s, 4),
        "inference_runtime_s": round(completed_unit_runtime_s, 4),
        "device": resolved_device,
        "artifacts": artifacts,
        "unit_results": unit_results,
        "label_distributions": label_distributions,
        "vector_dimensions": vector_dimensions,
        "summary_path": str(summary_path),
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
    limit: int | None = None,
    sample_size: int | None = None,
    sample_strategy: str = "head",
    seed: int = 7,
    resume: bool = True,
    force: bool = False,
    prewarm_models: bool = False,
    run_label: str | None = None,
) -> dict[str, Any]:
    sampling_config = SamplingConfig(
        limit=limit,
        sample_size=sample_size,
        sample_strategy=sample_strategy,
        seed=seed,
    )
    _validate_sampling_config(sampling_config)
    label_groups = _resolve_label_groups(model_names, zero_shot_label_config)

    report: dict[str, Any] = {
        "config": {
            "case_ids": case_ids,
            "model_names": model_names,
            "unit_types": unit_types,
            "output_dir": str(output_dir) if output_dir is not None else None,
            "zero_shot_label_config": str(zero_shot_label_config)
            if zero_shot_label_config is not None
            else None,
            "batch_size": batch_size,
            "max_length": max_length,
            "device": device,
            "case_dir": str(case_dir) if case_dir is not None else None,
            "resume": resume,
            "force": force,
            "prewarm_models": prewarm_models,
            "run_label": run_label,
            "sampling": asdict(sampling_config),
        },
        "cases": [],
    }
    for case_id in case_ids:
        case = resolve_case_artifacts(case_id, case_dir=case_dir)
        raw_units_by_type = load_units_for_case(case, unit_types=unit_types)
        units_by_type: dict[str, list[TextUnit]] = {}
        sampling_metadata: dict[str, dict[str, Any]] = {}
        for unit_type, units in raw_units_by_type.items():
            selected_units, metadata = _apply_sampling(units, config=sampling_config)
            units_by_type[unit_type] = selected_units
            sampling_metadata[unit_type] = metadata

        case_output_root = build_case_sidecar_output_dir(case_id, output_dir=output_dir)
        case_output_root.mkdir(parents=True, exist_ok=True)
        case_summary: dict[str, Any] = {
            "case_id": case_id,
            "input_root": str(case.input_root),
            "output_root": str(case_output_root),
            "sampling": sampling_metadata,
            "models": {},
        }

        for model_name in model_names:
            model = build_model(model_name, device=device)
            case_summary["models"][model_name] = _run_single_model_for_case(
                case=case,
                case_output_root=case_output_root,
                model_name=model_name,
                model=model,
                units_by_type=units_by_type,
                sampling_metadata=sampling_metadata,
                label_groups=label_groups,
                batch_size=batch_size,
                max_length=max_length,
                resume=resume,
                force=force,
                prewarm_models=prewarm_models,
                run_label=run_label,
            )

        report["cases"].append(case_summary)
    return report


def benchmark_model_sidecars(
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
    limit: int | None = None,
    sample_size: int | None = None,
    sample_strategy: str = "head",
    seed: int = 7,
    run_mode: str = "warm",
) -> dict[str, Any]:
    normalized_run_mode = str(run_mode or "warm").strip().lower() or "warm"
    if normalized_run_mode not in {"cold", "warm", "both"}:
        raise RuntimeError("Benchmark run mode must be one of: cold, warm, both.")

    run_labels = (
        ["cold", "warm"]
        if normalized_run_mode == "both"
        else [normalized_run_mode]
    )
    run_payloads: list[dict[str, Any]] = []
    for label in run_labels:
        payload = run_model_sidecars(
            case_ids=case_ids,
            model_names=model_names,
            unit_types=unit_types,
            output_dir=output_dir,
            zero_shot_label_config=zero_shot_label_config,
            batch_size=batch_size,
            max_length=max_length,
            device=device,
            case_dir=case_dir,
            limit=limit,
            sample_size=sample_size,
            sample_strategy=sample_strategy,
            seed=seed,
            resume=False,
            force=True,
            prewarm_models=label == "warm",
            run_label=label,
        )
        run_payloads.append({"run_label": label, "payload": payload})

    return {
        "run_mode": normalized_run_mode,
        "runs": run_payloads,
        "notes": [
            "Cold runs include model initialization inside the measured run.",
            "Warm runs call the model prewarm path before timing inference.",
            "Peak memory is approximate process-level RSS where available.",
        ],
    }
