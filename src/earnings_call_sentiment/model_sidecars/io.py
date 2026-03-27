"""Artifact discovery, unit loading, and output writing for model sidecars."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .models.base import ClassificationOutput, EmbeddingOutput, TextUnit

DEFAULT_SIDECAR_OUTPUT_ROOT = Path("outputs")

_CLASSIFICATION_FILE_NAMES = {
    "chunks": "chunk_scores.jsonl",
    "guidance_spans": "guidance_span_scores.jsonl",
    "qa_answers": "qa_answer_scores.jsonl",
    "speaker_turns": "speaker_turn_scores.jsonl",
}

_EMBEDDING_FILE_NAMES = {
    "chunks": "chunk_embeddings.jsonl",
    "guidance_spans": "guidance_span_embeddings.jsonl",
    "qa_answers": "qa_answer_embeddings.jsonl",
    "speaker_turns": "speaker_turn_embeddings.jsonl",
}

_SIMILARITY_FILE_NAMES = {
    "chunks": "chunk_similarity.json",
    "guidance_spans": "guidance_similarity.json",
    "qa_answers": "qa_similarity.json",
    "speaker_turns": "speaker_turn_similarity.json",
}


@dataclass(frozen=True)
class CaseArtifacts:
    case_id: str
    input_root: Path
    layout: str
    chunks_scored_path: Path | None
    guidance_path: Path | None
    guidance_revision_path: Path | None
    qa_pairs_path: Path | None
    transcript_sectioned_path: Path | None
    transcript_json_path: Path | None
    segment_metadata_path: Path | None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_sidecar_output_root() -> Path:
    return repo_root() / DEFAULT_SIDECAR_OUTPUT_ROOT


def build_case_sidecar_output_dir(
    case_id: str,
    *,
    output_dir: str | Path | None = None,
) -> Path:
    base = Path(output_dir) if output_dir is not None else default_sidecar_output_root()
    return base.expanduser().resolve() / case_id / "model_sidecars"


def build_case_benchmark_output_dir(
    case_id: str,
    *,
    output_dir: str | Path | None = None,
) -> Path:
    return build_case_sidecar_output_dir(case_id, output_dir=output_dir) / "benchmarks"


def _resolve_existing_path(base: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        path = base / candidate
        if path.exists() and path.is_file():
            return path
    return None


def resolve_case_artifacts(
    case_id: str,
    *,
    case_dir: str | Path | None = None,
) -> CaseArtifacts:
    repo = repo_root()
    candidates = (
        [Path(case_dir).expanduser().resolve()]
        if case_dir is not None
        else [
            repo / "outputs" / case_id,
            repo / "outputs" / "downstream_decision_eval" / case_id,
            repo / "data" / "demo_cases" / case_id / "processed",
        ]
    )

    for candidate in candidates:
        chunks_scored_path = _resolve_existing_path(
            candidate,
            ["chunks_scored.csv", "chunks/chunks_scored.csv"],
        )
        guidance_path = _resolve_existing_path(
            candidate,
            ["guidance.csv", "signals/guidance.csv"],
        )
        qa_pairs_path = _resolve_existing_path(
            candidate,
            ["qa_pairs.json", "qa_pairs/qa_pairs.json"],
        )
        transcript_sectioned_path = _resolve_existing_path(
            candidate,
            [
                "transcript_sectioned.json",
                "transcript_text/transcript_sectioned.json",
            ],
        )
        transcript_json_path = _resolve_existing_path(
            candidate,
            ["transcript.json", "transcript_text/transcript.json"],
        )
        segment_metadata_path = _resolve_existing_path(
            candidate,
            ["segment_metadata.json", "chunks/segment_metadata.json"],
        )
        guidance_revision_path = _resolve_existing_path(
            candidate,
            ["guidance_revision.csv", "signals/guidance_revision.csv"],
        )
        if any(
            path is not None
            for path in (
                chunks_scored_path,
                guidance_path,
                qa_pairs_path,
                transcript_sectioned_path,
                transcript_json_path,
                segment_metadata_path,
            )
        ):
            return CaseArtifacts(
                case_id=case_id,
                input_root=candidate,
                layout="processed_case",
                chunks_scored_path=chunks_scored_path,
                guidance_path=guidance_path,
                guidance_revision_path=guidance_revision_path,
                qa_pairs_path=qa_pairs_path,
                transcript_sectioned_path=transcript_sectioned_path,
                transcript_json_path=transcript_json_path,
                segment_metadata_path=segment_metadata_path,
            )

    raise RuntimeError(
        "Could not locate an existing processed case for "
        f"'{case_id}'. Checked outputs/<case_id>, outputs/downstream_decision_eval/<case_id>, "
        "and data/demo_cases/<case_id>/processed."
    )


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).replace("\n", " ").strip()


def _coerce_float(value: Any) -> float | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_segment_rows(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    payload = _read_json(path)
    if isinstance(payload, dict):
        rows = payload.get("segments", [])
        return [row for row in rows if isinstance(row, dict)]
    return []


def _load_transcript_blocks(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    payload = _read_json(path)
    if isinstance(payload, dict):
        rows = payload.get("blocks", [])
        return [row for row in rows if isinstance(row, dict)]
    return []


def _match_segment_context(
    *,
    start_time: float | None,
    end_time: float | None,
    segment_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if start_time is None or end_time is None or not segment_rows:
        return {}

    best_overlap = 0.0
    best_row: dict[str, Any] = {}
    for row in segment_rows:
        row_start = _coerce_float(row.get("start"))
        row_end = _coerce_float(row.get("end"))
        if row_start is None or row_end is None:
            continue
        overlap = max(0.0, min(end_time, row_end) - max(start_time, row_start))
        if overlap > best_overlap:
            best_overlap = overlap
            best_row = row
    return best_row


def _require_path(path: Path | None, *, case_id: str, unit_type: str, artifact: str) -> Path:
    if path is None or not path.exists():
        raise RuntimeError(
            f"Case '{case_id}' does not include {artifact}, so '{unit_type}' sidecars cannot run."
        )
    return path


def load_units_for_case(
    case: CaseArtifacts,
    *,
    unit_types: list[str],
) -> dict[str, list[TextUnit]]:
    units_by_type: dict[str, list[TextUnit]] = {}
    segment_rows = _load_segment_rows(case.segment_metadata_path)
    for unit_type in unit_types:
        if unit_type == "chunks":
            units_by_type[unit_type] = _load_chunk_units(case, segment_rows=segment_rows)
        elif unit_type == "guidance_spans":
            units_by_type[unit_type] = _load_guidance_units(case, segment_rows=segment_rows)
        elif unit_type == "qa_answers":
            units_by_type[unit_type] = _load_qa_answer_units(case)
        elif unit_type == "speaker_turns":
            units_by_type[unit_type] = _load_speaker_turn_units(case)
        else:
            raise RuntimeError(f"Unsupported unit type '{unit_type}'.")
    return units_by_type


def _load_chunk_units(
    case: CaseArtifacts,
    *,
    segment_rows: list[dict[str, Any]],
) -> list[TextUnit]:
    path = _require_path(
        case.chunks_scored_path,
        case_id=case.case_id,
        unit_type="chunks",
        artifact="chunks_scored.csv",
    )
    frame = pd.read_csv(path, keep_default_na=False)
    units: list[TextUnit] = []
    for index, (_, row) in enumerate(frame.iterrows(), start=1):
        text = _normalize_text(row.get("text"))
        if not text:
            continue
        segment_row = segment_rows[index - 1] if index - 1 < len(segment_rows) else {}
        units.append(
            TextUnit(
                case_id=case.case_id,
                unit_type="chunks",
                source_id=str(segment_row.get("segment_id", f"chunk_{index:04d}")),
                section=_normalize_text(segment_row.get("section")) or None,
                speaker=_normalize_text(segment_row.get("speaker")) or None,
                text=text,
                metadata={
                    "start": _coerce_float(row.get("start")),
                    "end": _coerce_float(row.get("end")),
                    "sentiment": _normalize_text(row.get("sentiment")),
                    "score": _coerce_float(row.get("score")),
                    "signed_score": _coerce_float(row.get("signed_score")),
                    "speaker_role": _normalize_text(segment_row.get("speaker_role")),
                },
            )
        )
    if not units:
        raise RuntimeError(f"Case '{case.case_id}' has no usable chunk rows.")
    return units


def _load_guidance_units(
    case: CaseArtifacts,
    *,
    segment_rows: list[dict[str, Any]],
) -> list[TextUnit]:
    path = _require_path(
        case.guidance_path,
        case_id=case.case_id,
        unit_type="guidance_spans",
        artifact="guidance.csv",
    )
    frame = pd.read_csv(path, keep_default_na=False)
    units: list[TextUnit] = []
    for index, (_, row) in enumerate(frame.iterrows(), start=1):
        text = _normalize_text(row.get("text"))
        if not text:
            continue
        start_time = _coerce_float(row.get("start"))
        end_time = _coerce_float(row.get("end"))
        matched = _match_segment_context(
            start_time=start_time,
            end_time=end_time,
            segment_rows=segment_rows,
        )
        units.append(
            TextUnit(
                case_id=case.case_id,
                unit_type="guidance_spans",
                source_id=f"guidance_span_{index:04d}",
                section=_normalize_text(matched.get("section")) or None,
                speaker=_normalize_text(matched.get("speaker")) or None,
                text=text,
                metadata={
                    "start": start_time,
                    "end": end_time,
                    "topic": _normalize_text(row.get("topic")),
                    "period": _normalize_text(row.get("period")),
                    "guidance_strength": _coerce_float(row.get("guidance_strength")),
                    "matched_cues": _normalize_text(row.get("matched_cues")),
                    "speaker_role": _normalize_text(matched.get("speaker_role")),
                },
            )
        )
    if not units:
        raise RuntimeError(f"Case '{case.case_id}' has no usable guidance spans.")
    return units


def _load_qa_answer_units(case: CaseArtifacts) -> list[TextUnit]:
    path = _require_path(
        case.qa_pairs_path,
        case_id=case.case_id,
        unit_type="qa_answers",
        artifact="qa_pairs.json",
    )
    payload = _read_json(path)
    rows = payload.get("qa_pairs", []) if isinstance(payload, dict) else []
    units: list[TextUnit] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = _normalize_text(row.get("answer_text"))
        if not text:
            continue
        qa_pair_id = int(row.get("qa_pair_id", len(units) + 1))
        speakers = [
            _normalize_text(value)
            for value in row.get("answer_speakers", [])
            if _normalize_text(value)
        ]
        units.append(
            TextUnit(
                case_id=case.case_id,
                unit_type="qa_answers",
                source_id=f"qa_answer_{qa_pair_id:04d}",
                section="question_and_answer",
                speaker="; ".join(speakers) or None,
                text=text,
                metadata={
                    "qa_pair_id": qa_pair_id,
                    "question_speaker": _normalize_text(row.get("question_speaker")),
                    "question_text": _normalize_text(row.get("question_text")),
                    "answer_speakers": speakers,
                    "source_doc": _normalize_text(row.get("source_doc")),
                },
            )
        )
    if not units:
        raise RuntimeError(f"Case '{case.case_id}' has no usable Q&A answers.")
    return units


def _load_speaker_turn_units(case: CaseArtifacts) -> list[TextUnit]:
    path = _require_path(
        case.transcript_sectioned_path,
        case_id=case.case_id,
        unit_type="speaker_turns",
        artifact="transcript_sectioned.json",
    )
    rows = _load_transcript_blocks(path)
    units: list[TextUnit] = []
    for row in rows:
        text = _normalize_text(row.get("text"))
        if not text:
            continue
        block_id = int(row.get("block_id", len(units)))
        units.append(
            TextUnit(
                case_id=case.case_id,
                unit_type="speaker_turns",
                source_id=f"speaker_turn_{block_id:04d}",
                section=_normalize_text(row.get("section")) or None,
                speaker=_normalize_text(row.get("speaker")) or None,
                text=text,
                metadata={
                    "block_id": block_id,
                    "speaker_role": _normalize_text(row.get("speaker_role")),
                    "speaker_title": _normalize_text(row.get("speaker_title")),
                    "timestamp": _normalize_text(row.get("timestamp")),
                    "source_doc": _normalize_text(row.get("source_doc")),
                },
            )
        )
    if not units:
        raise RuntimeError(f"Case '{case.case_id}' has no usable speaker turns.")
    return units


def load_prior_guidance_pairs(case: CaseArtifacts) -> list[dict[str, Any]]:
    path = case.guidance_revision_path
    if path is None or not path.exists():
        return []
    frame = pd.read_csv(path, keep_default_na=False)
    pairs: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        current_text = _normalize_text(row.get("current_text_snippet"))
        prior_text = _normalize_text(row.get("prior_text_snippet"))
        if not current_text or not prior_text:
            continue
        pairs.append(
            {
                "row_id": _normalize_text(row.get("row_id")),
                "topic": _normalize_text(row.get("topic")),
                "period": _normalize_text(row.get("period")),
                "revision_label": _normalize_text(row.get("revision_label")),
                "current_text": current_text,
                "prior_text": prior_text,
            }
        )
    return pairs


def model_output_dir(output_root: Path, model_name: str) -> Path:
    return output_root / model_name


def classification_output_path(output_root: Path, model_name: str, unit_type: str) -> Path:
    return model_output_dir(output_root, model_name) / _CLASSIFICATION_FILE_NAMES[unit_type]


def embedding_output_path(output_root: Path, model_name: str, unit_type: str) -> Path:
    return model_output_dir(output_root, model_name) / _EMBEDDING_FILE_NAMES[unit_type]


def similarity_output_path(output_root: Path, model_name: str, unit_type: str) -> Path:
    return model_output_dir(output_root, model_name) / _SIMILARITY_FILE_NAMES[unit_type]


def run_summary_path(output_root: Path, model_name: str) -> Path:
    return model_output_dir(output_root, model_name) / "run_summary.json"


def benchmark_json_path(case_id: str, *, output_root: str | Path | None = None) -> Path:
    return build_case_benchmark_output_dir(case_id, output_dir=output_root) / "model_sidecars_benchmark.json"


def benchmark_markdown_path(case_id: str, *, output_root: str | Path | None = None) -> Path:
    return build_case_benchmark_output_dir(case_id, output_dir=output_root) / "model_sidecars_benchmark.md"


def artifact_is_complete(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def expected_unit_artifact_paths(
    *,
    output_root: Path,
    model_name: str,
    unit_type: str,
    output_kind: str,
) -> dict[str, Path]:
    if output_kind == "classification":
        return {"output": classification_output_path(output_root, model_name, unit_type)}
    if output_kind == "embedding":
        return {
            "output": embedding_output_path(output_root, model_name, unit_type),
            "similarity": similarity_output_path(output_root, model_name, unit_type),
        }
    raise RuntimeError(f"Unsupported output kind '{output_kind}'.")


def unit_output_complete(
    *,
    output_root: Path,
    model_name: str,
    unit_type: str,
    output_kind: str,
) -> bool:
    artifacts = expected_unit_artifact_paths(
        output_root=output_root,
        model_name=model_name,
        unit_type=unit_type,
        output_kind=output_kind,
    )
    return all(artifact_is_complete(path) for path in artifacts.values())


def completion_rule_for(output_kind: str) -> str:
    if output_kind == "classification":
        return "Complete when the final unit JSONL exists and is non-empty."
    if output_kind == "embedding":
        return (
            "Complete when the final embedding JSONL and similarity JSON both exist "
            "and are non-empty."
        )
    raise RuntimeError(f"Unsupported output kind '{output_kind}'.")


def _timestamp_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def _temp_output_path(path: Path) -> Path:
    return path.parent / f".{path.name}.inprogress"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _temp_output_path(path)
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _temp_output_path(path)
    with temp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def write_model_run_summary(
    *,
    output_root: Path,
    model_name: str,
    payload: dict[str, Any],
) -> Path:
    path = run_summary_path(output_root, model_name)
    _write_json(path, payload)
    return path


def write_classification_unit_output(
    *,
    case_id: str,
    model_name: str,
    model_id: str,
    output_root: Path,
    unit_type: str,
    rows: list[ClassificationOutput],
) -> dict[str, Any]:
    unit_records: list[dict[str, Any]] = []
    top_label_counts: dict[str, int] = {}
    for output in rows:
        if output.scores:
            top_label = output.scores[0].label
            top_label_counts[top_label] = top_label_counts.get(top_label, 0) + 1
        for score in output.scores:
            unit_records.append(
                {
                    "case_id": output.unit.case_id,
                    "unit_type": output.unit.unit_type,
                    "source_id": output.unit.source_id,
                    "section": output.unit.section,
                    "speaker": output.unit.speaker,
                    "text": output.unit.text,
                    "model_name": model_name,
                    "label": score.label,
                    "score": score.score,
                    "rank": score.rank,
                    "metadata": {
                        "model_id": model_id,
                        "source_metadata": output.unit.metadata,
                        **score.metadata,
                    },
                }
            )

    path = classification_output_path(output_root, model_name, unit_type)
    _write_jsonl(path, unit_records)
    return {
        "case_id": case_id,
        "unit_type": unit_type,
        "path": path,
        "unit_count": len(rows),
        "record_count": len(unit_records),
        "label_distribution": top_label_counts,
        "completed_at": _timestamp_utc(),
        "completion_rule": completion_rule_for("classification"),
    }


def write_embedding_unit_output(
    *,
    case_id: str,
    model_name: str,
    model_id: str,
    output_root: Path,
    unit_type: str,
    rows: list[EmbeddingOutput],
    similarity_payload: dict[str, Any],
) -> dict[str, Any]:
    unit_records: list[dict[str, Any]] = []
    dimension = len(rows[0].vector) if rows else 0
    for output in rows:
        unit_records.append(
            {
                "case_id": output.unit.case_id,
                "unit_type": output.unit.unit_type,
                "source_id": output.unit.source_id,
                "section": output.unit.section,
                "speaker": output.unit.speaker,
                "text": output.unit.text,
                "model_name": model_name,
                "vector_dimension": len(output.vector),
                "embedding": [round(float(value), 6) for value in output.vector],
                "metadata": {
                    "model_id": model_id,
                    "source_metadata": output.unit.metadata,
                },
            }
        )

    path = embedding_output_path(output_root, model_name, unit_type)
    similarity_path = similarity_output_path(output_root, model_name, unit_type)
    _write_jsonl(path, unit_records)
    _write_json(similarity_path, similarity_payload)
    return {
        "case_id": case_id,
        "unit_type": unit_type,
        "path": path,
        "similarity_path": similarity_path,
        "unit_count": len(rows),
        "record_count": len(unit_records),
        "vector_dimension": dimension,
        "similarity_mode": similarity_payload.get("mode"),
        "completed_at": _timestamp_utc(),
        "completion_rule": completion_rule_for("embedding"),
    }


def write_classification_outputs(
    *,
    case_id: str,
    model_name: str,
    model_id: str,
    output_root: Path,
    outputs_by_unit: dict[str, list[ClassificationOutput]],
    runtime_s: float,
) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    summary: dict[str, Any] = {
        "case_id": case_id,
        "model_name": model_name,
        "model_id": model_id,
        "runtime_s": round(runtime_s, 4),
        "output_kind": "classification",
        "unit_counts": {},
        "label_distributions": {},
    }
    for unit_type, rows in outputs_by_unit.items():
        result = write_classification_unit_output(
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            output_root=output_root,
            unit_type=unit_type,
            rows=rows,
        )
        artifacts[unit_type] = result["path"]
        summary["unit_counts"][unit_type] = result["unit_count"]
        summary["label_distributions"][unit_type] = result["label_distribution"]

    summary_path = write_model_run_summary(
        output_root=output_root,
        model_name=model_name,
        payload=summary,
    )
    artifacts["run_summary"] = summary_path
    return artifacts


def write_embedding_outputs(
    *,
    case_id: str,
    model_name: str,
    model_id: str,
    output_root: Path,
    outputs_by_unit: dict[str, list[EmbeddingOutput]],
    similarity_by_unit: dict[str, dict[str, Any]],
    runtime_s: float,
) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    summary: dict[str, Any] = {
        "case_id": case_id,
        "model_name": model_name,
        "model_id": model_id,
        "runtime_s": round(runtime_s, 4),
        "output_kind": "embedding",
        "unit_counts": {},
        "vector_dimensions": {},
    }
    for unit_type, rows in outputs_by_unit.items():
        similarity_payload = similarity_by_unit.get(unit_type, {})
        result = write_embedding_unit_output(
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            output_root=output_root,
            unit_type=unit_type,
            rows=rows,
            similarity_payload=similarity_payload,
        )
        artifacts[unit_type] = result["path"]
        artifacts[f"{unit_type}_similarity"] = result["similarity_path"]
        summary["unit_counts"][unit_type] = result["unit_count"]
        summary["vector_dimensions"][unit_type] = result["vector_dimension"]

    summary_path = write_model_run_summary(
        output_root=output_root,
        model_name=model_name,
        payload=summary,
    )
    artifacts["run_summary"] = summary_path
    return artifacts
