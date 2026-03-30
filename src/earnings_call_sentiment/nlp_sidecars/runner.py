"""Execution helpers for optional NLP sidecar runs."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from .base import ClassificationResult, EmbeddingResult
from .config import load_zero_shot_label_groups, resolve_cache_dir
from .evaluate import (
    build_classification_disagreement_report,
    build_embedding_disagreement_report,
    build_markdown_summary,
    write_case_evaluation_summary,
)
from .io import load_text_units, model_output_dir, write_model_outputs
from .models import build_model, model_metadata_from_results


def _write_failure_summary(target_dir: Path, *, model_name: str, model_kind: str, error: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "model_name": model_name,
                "model_kind": model_kind,
                "status": "error",
                "error": error,
                "notes": [
                    "Sidecar execution failed gracefully.",
                    "Deterministic transcript-backed outputs remain canonical.",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_sidecar_models(
    *,
    case_id: str,
    artifact_inputs: dict[str, Path],
    unit_types: list[str],
    model_names: list[str],
    output_root: str | Path | None = None,
    device: str = "auto",
    batch_size: int = 8,
    max_length: int = 384,
    smoke_limit: int | None = None,
    prewarm: bool = False,
    resume: bool = True,
    force: bool = False,
    zero_shot_config: str | Path | None = None,
) -> dict[str, Any]:
    units = load_text_units(
        case_id=case_id,
        artifact_inputs=artifact_inputs,
        unit_types=unit_types,
        smoke_limit=smoke_limit,
    )
    unit_type_counts: dict[str, int] = {}
    for unit in units:
        unit_type_counts[unit.unit_type] = unit_type_counts.get(unit.unit_type, 0) + 1

    cache_dir = resolve_cache_dir()
    zero_shot_labels = load_zero_shot_label_groups(zero_shot_config) if zero_shot_config else None
    outputs: dict[str, Any] = {
        "case_id": case_id,
        "units_loaded": len(units),
        "unit_type_counts": unit_type_counts,
        "models": [],
    }

    for model_name in model_names:
        model = build_model(model_name, device=device, cache_dir=cache_dir)
        target_dir = model_output_dir(case_id=case_id, model_name=model_name, output_root=output_root)
        existing_summary = target_dir / "run_summary.json"
        existing_rows = target_dir / "scored_rows.csv"
        if resume and not force and existing_summary.exists() and existing_rows.exists():
            payload = json.loads(existing_summary.read_text(encoding="utf-8"))
            if payload.get("status") == "ok":
                outputs["models"].append({"model_name": model_name, "status": "skipped_resume"})
                continue

        try:
            prewarm_metadata = model.prewarm() if prewarm else {}
            started = time.perf_counter()
            if model.output_kind == "classification":
                classification_results = model.predict(
                    units,
                    batch_size=batch_size,
                    max_length=max_length,
                    label_groups=zero_shot_labels,
                )
                runtime_s = round(time.perf_counter() - started, 4)
                disagreement = build_classification_disagreement_report(
                    model_name=model_name,
                    results=classification_results,
                )
                run_summary = {
                    "case_id": case_id,
                    "model_name": model_name,
                    "model_kind": model.output_kind,
                    "status": "ok",
                    "device": prewarm_metadata.get("device", device),
                    "runtime_s": runtime_s,
                    "units_processed": len(classification_results),
                    "rows_per_second": round(len(classification_results) / runtime_s, 4) if runtime_s else 0.0,
                    "unit_type_counts": unit_type_counts,
                    "smoke_limit": smoke_limit,
                    "batch_size": batch_size,
                    "max_length": max_length,
                    "notes": [
                        "Optional NLP sidecar run completed without changing deterministic outputs.",
                        "These results are supporting evidence only.",
                    ],
                }
                model_metadata = {**prewarm_metadata, **model_metadata_from_results(classification_results)}
                markdown = build_markdown_summary(
                    model_name=model_name,
                    model_kind=model.output_kind,
                    run_summary=run_summary,
                    disagreement_report=disagreement,
                )
                paths = write_model_outputs(
                    case_id=case_id,
                    model_name=model_name,
                    model_kind=model.output_kind,
                    run_summary=run_summary,
                    model_metadata=model_metadata,
                    markdown_summary=markdown,
                    disagreement_report=disagreement,
                    classification_results=classification_results,
                    output_root=output_root,
                )
            else:
                embedding_results = model.embed(units, batch_size=batch_size)
                runtime_s = round(time.perf_counter() - started, 4)
                disagreement = build_embedding_disagreement_report(
                    model_name=model_name,
                    results=embedding_results,
                )
                run_summary = {
                    "case_id": case_id,
                    "model_name": model_name,
                    "model_kind": model.output_kind,
                    "status": "ok",
                    "device": prewarm_metadata.get("device", device),
                    "runtime_s": runtime_s,
                    "units_processed": len(embedding_results),
                    "rows_per_second": round(len(embedding_results) / runtime_s, 4) if runtime_s else 0.0,
                    "unit_type_counts": unit_type_counts,
                    "smoke_limit": smoke_limit,
                    "batch_size": batch_size,
                    "notes": [
                        "Optional NLP embedding sidecar completed without changing deterministic outputs.",
                        "Embeddings are similarity aids only.",
                    ],
                }
                model_metadata = {**prewarm_metadata, **model_metadata_from_results(embedding_results)}
                markdown = build_markdown_summary(
                    model_name=model_name,
                    model_kind=model.output_kind,
                    run_summary=run_summary,
                    disagreement_report=disagreement,
                )
                paths = write_model_outputs(
                    case_id=case_id,
                    model_name=model_name,
                    model_kind=model.output_kind,
                    run_summary=run_summary,
                    model_metadata=model_metadata,
                    markdown_summary=markdown,
                    disagreement_report=disagreement,
                    embedding_results=embedding_results,
                    output_root=output_root,
                )
            outputs["models"].append(
                {
                    "model_name": model_name,
                    "status": "ok",
                    "paths": {key: str(value) for key, value in paths.items()},
                }
            )
        except Exception as exc:
            _write_failure_summary(
                target_dir,
                model_name=model_name,
                model_kind=model.output_kind,
                error=str(exc),
            )
            outputs["models"].append({"model_name": model_name, "status": "error", "error": str(exc)})

    evaluation_paths = write_case_evaluation_summary(case_id=case_id, output_root=output_root)
    outputs["evaluation"] = {key: str(value) for key, value in evaluation_paths.items()}
    return outputs
