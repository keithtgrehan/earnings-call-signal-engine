"""Artifact loading and output writing for optional NLP sidecars."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from .base import (
    ClassificationResult,
    EmbeddingResult,
    TextUnit,
    normalize_label,
    normalize_polarity_label,
)
from .config import default_output_root


def _clean_text(value: Any) -> str:
    return str(value or "").replace("\n", " ").strip()


def _coerce_float(value: Any) -> float | None:
    text = _clean_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def build_artifact_inputs(
    *,
    case_id: str,
    demo_case_root: str | Path | None = None,
    chunks_csv: str | Path | None = None,
    guidance_csv: str | Path | None = None,
    qa_pairs_json: str | Path | None = None,
) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    if demo_case_root is not None:
        base = Path(demo_case_root).expanduser().resolve()
        resolved["chunks"] = base / "processed" / "chunks" / "chunks_scored.csv"
        resolved["guidance_spans"] = base / "processed" / "signals" / "guidance.csv"
        resolved["qa_answers"] = base / "processed" / "qa_pairs" / "qa_pairs.json"

    explicit = {
        "chunks": chunks_csv,
        "guidance_spans": guidance_csv,
        "qa_answers": qa_pairs_json,
    }
    for unit_type, candidate in explicit.items():
        if candidate is not None:
            resolved[unit_type] = Path(candidate).expanduser().resolve()

    available = {key: path for key, path in resolved.items() if path.exists() and path.is_file()}
    if not available:
        raise RuntimeError(
            f"No usable sidecar input artifacts were found for case '{case_id}'. "
            "Provide --demo-case-root or explicit artifact paths."
        )
    return available


def _load_chunks_units(case_id: str, path: Path) -> list[TextUnit]:
    frame = pd.read_csv(path, keep_default_na=False)
    rows: list[TextUnit] = []
    for idx, row in enumerate(frame.to_dict(orient="records"), start=1):
        text = _clean_text(row.get("text"))
        if not text:
            continue
        rows.append(
            TextUnit(
                case_id=case_id,
                unit_type="chunks",
                unit_id=f"chunk_{idx:04d}",
                text=text,
                source_artifact=str(path),
                start_time_s=_coerce_float(row.get("start")),
                end_time_s=_coerce_float(row.get("end")),
                deterministic_label=normalize_label(row.get("sentiment")) or None,
                deterministic_score=_coerce_float(row.get("score")),
                deterministic_signed_score=_coerce_float(row.get("signed_score")),
                deterministic_metadata={
                    "positive_prob": _coerce_float(row.get("positive_prob")),
                    "negative_prob": _coerce_float(row.get("negative_prob")),
                },
            )
        )
    return rows


def _load_guidance_units(case_id: str, path: Path) -> list[TextUnit]:
    frame = pd.read_csv(path, keep_default_na=False)
    rows: list[TextUnit] = []
    for idx, row in enumerate(frame.to_dict(orient="records"), start=1):
        text = _clean_text(row.get("text"))
        if not text:
            continue
        rows.append(
            TextUnit(
                case_id=case_id,
                unit_type="guidance_spans",
                unit_id=f"guidance_{idx:04d}",
                text=text,
                source_artifact=str(path),
                start_time_s=_coerce_float(row.get("start")),
                end_time_s=_coerce_float(row.get("end")),
                deterministic_label=normalize_label(row.get("sentiment")) or None,
                deterministic_score=_coerce_float(row.get("guidance_strength")) or _coerce_float(row.get("score")),
                deterministic_metadata={
                    "topic": _clean_text(row.get("topic")),
                    "period": _clean_text(row.get("period")),
                    "matched_cues": _clean_text(row.get("matched_cues")),
                },
            )
        )
    return rows


def _extract_qa_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("qa_pairs"), list):
            return [item for item in payload["qa_pairs"] if isinstance(item, dict)]
        for value in payload.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _load_qa_units(case_id: str, path: Path) -> list[TextUnit]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[TextUnit] = []
    for idx, row in enumerate(_extract_qa_rows(payload), start=1):
        answer_text = _clean_text(row.get("answer_text"))
        if not answer_text:
            continue
        answer_speakers = row.get("answer_speakers")
        speaker = ""
        if isinstance(answer_speakers, list):
            speaker = ", ".join(_clean_text(item) for item in answer_speakers if _clean_text(item))
        rows.append(
            TextUnit(
                case_id=case_id,
                unit_type="qa_answers",
                unit_id=f"qa_answer_{int(row.get('qa_pair_id', idx)):04d}",
                text=answer_text,
                source_artifact=str(path),
                section=_clean_text(row.get("source_doc")) or "qa_pairs",
                speaker=speaker or None,
                deterministic_metadata={
                    "question_speaker": _clean_text(row.get("question_speaker")),
                    "question_text": _clean_text(row.get("question_text")),
                },
            )
        )
    return rows


def load_text_units(
    *,
    case_id: str,
    artifact_inputs: dict[str, Path],
    unit_types: list[str],
    smoke_limit: int | None = None,
) -> list[TextUnit]:
    loaders = {
        "chunks": _load_chunks_units,
        "guidance_spans": _load_guidance_units,
        "qa_answers": _load_qa_units,
    }
    units: list[TextUnit] = []
    for unit_type in unit_types:
        if unit_type not in loaders:
            raise RuntimeError(f"Unsupported NLP sidecar unit type: {unit_type}")
        path = artifact_inputs.get(unit_type)
        if path is None:
            raise RuntimeError(
                f"Requested unit type '{unit_type}' is unavailable because its artifact path was not provided."
            )
        loaded = loaders[unit_type](case_id, path)
        if smoke_limit is not None and smoke_limit > 0:
            loaded = loaded[:smoke_limit]
        units.extend(loaded)
    if not units:
        raise RuntimeError("No text units were loaded from the requested artifacts.")
    return units


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def model_output_dir(
    *,
    case_id: str,
    model_name: str,
    output_root: str | Path | None = None,
) -> Path:
    base = Path(output_root).expanduser().resolve() if output_root else default_output_root().resolve()
    return base / case_id / "model_sidecars" / model_name


def evaluation_output_dir(*, case_id: str, output_root: str | Path | None = None) -> Path:
    base = Path(output_root).expanduser().resolve() if output_root else default_output_root().resolve()
    return base / case_id / "model_sidecars" / "evaluation"


def build_classification_rows(results: list[ClassificationResult], *, model_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        top = result.scores[0] if result.scores else None
        rows.append(
            {
                "case_id": result.unit.case_id,
                "unit_type": result.unit.unit_type,
                "unit_id": result.unit.unit_id,
                "source_artifact": result.unit.source_artifact,
                "section": result.unit.section or "",
                "speaker": result.unit.speaker or "",
                "start_time_s": result.unit.start_time_s,
                "end_time_s": result.unit.end_time_s,
                "text": result.unit.text,
                "text_char_len": len(result.unit.text),
                "model_name": model_name,
                "output_kind": "classification",
                "top_label": top.label if top else "",
                "top_score": top.score if top else None,
                "comparable_label": result.comparable_label or "",
                "scores_json": _json_dumps([asdict(score) for score in result.scores]),
                "group_top_labels_json": _json_dumps(result.metadata.get("group_top_labels", {})),
                "deterministic_label": result.unit.deterministic_label or "",
                "deterministic_polarity": normalize_polarity_label(result.unit.deterministic_label),
                "deterministic_score": result.unit.deterministic_score,
                "deterministic_signed_score": result.unit.deterministic_signed_score,
                "deterministic_metadata_json": _json_dumps(result.unit.deterministic_metadata),
            }
        )
    return rows


def build_embedding_rows(results: list[EmbeddingResult], *, model_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    vectors: list[dict[str, Any]] = []
    for result in results:
        vector = result.vector
        norm = sum(value * value for value in vector) ** 0.5 if vector else 0.0
        rows.append(
            {
                "case_id": result.unit.case_id,
                "unit_type": result.unit.unit_type,
                "unit_id": result.unit.unit_id,
                "source_artifact": result.unit.source_artifact,
                "section": result.unit.section or "",
                "speaker": result.unit.speaker or "",
                "start_time_s": result.unit.start_time_s,
                "end_time_s": result.unit.end_time_s,
                "text": result.unit.text,
                "text_char_len": len(result.unit.text),
                "model_name": model_name,
                "output_kind": "embedding",
                "embedding_dim": len(vector),
                "embedding_norm": round(norm, 6),
                "deterministic_label": result.unit.deterministic_label or "",
                "deterministic_polarity": normalize_polarity_label(result.unit.deterministic_label),
                "deterministic_metadata_json": _json_dumps(result.unit.deterministic_metadata),
            }
        )
        vectors.append(
            {
                "unit_id": result.unit.unit_id,
                "vector": vector,
                "metadata": result.metadata,
            }
        )
    return rows, vectors


def write_model_outputs(
    *,
    case_id: str,
    model_name: str,
    model_kind: str,
    run_summary: dict[str, Any],
    model_metadata: dict[str, Any],
    markdown_summary: str,
    disagreement_report: dict[str, Any],
    classification_results: list[ClassificationResult] | None = None,
    embedding_results: list[EmbeddingResult] | None = None,
    output_root: str | Path | None = None,
) -> dict[str, Path]:
    target_dir = model_output_dir(case_id=case_id, model_name=model_name, output_root=output_root)
    target_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {
        "run_summary": target_dir / "run_summary.json",
        "model_metadata": target_dir / "model_metadata.json",
        "summary_md": target_dir / "summary.md",
        "disagreement_report": target_dir / "disagreement_report.json",
    }

    _write_json(paths["run_summary"], run_summary)
    _write_json(paths["model_metadata"], model_metadata)
    _write_json(paths["disagreement_report"], disagreement_report)
    paths["summary_md"].write_text(markdown_summary, encoding="utf-8")

    if model_kind == "classification":
        rows = build_classification_rows(classification_results or [], model_name=model_name)
        paths["scored_rows"] = target_dir / "scored_rows.csv"
        _write_csv(
            paths["scored_rows"],
            rows,
            fieldnames=[
                "case_id",
                "unit_type",
                "unit_id",
                "source_artifact",
                "section",
                "speaker",
                "start_time_s",
                "end_time_s",
                "text",
                "text_char_len",
                "model_name",
                "output_kind",
                "top_label",
                "top_score",
                "comparable_label",
                "scores_json",
                "group_top_labels_json",
                "deterministic_label",
                "deterministic_polarity",
                "deterministic_score",
                "deterministic_signed_score",
                "deterministic_metadata_json",
            ],
        )
    else:
        rows, vectors = build_embedding_rows(embedding_results or [], model_name=model_name)
        paths["scored_rows"] = target_dir / "scored_rows.csv"
        paths["embeddings_json"] = target_dir / "embeddings.json"
        _write_csv(
            paths["scored_rows"],
            rows,
            fieldnames=[
                "case_id",
                "unit_type",
                "unit_id",
                "source_artifact",
                "section",
                "speaker",
                "start_time_s",
                "end_time_s",
                "text",
                "text_char_len",
                "model_name",
                "output_kind",
                "embedding_dim",
                "embedding_norm",
                "deterministic_label",
                "deterministic_polarity",
                "deterministic_metadata_json",
            ],
        )
        _write_json(paths["embeddings_json"], {"case_id": case_id, "rows": vectors})

    return paths
