"""Evaluation helpers for optional model-sidecar outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import build_case_sidecar_output_dir
from .models.registry import AVAILABLE_MODEL_NAMES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _normalize_sentiment_label(label: str) -> str:
    lowered = str(label or "").strip().lower()
    if "positive" in lowered:
        return "positive"
    if "negative" in lowered:
        return "negative"
    if "neutral" in lowered:
        return "neutral"
    return lowered or "unknown"


def _metadata_source(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata", {})
    if isinstance(metadata, dict):
        source_metadata = metadata.get("source_metadata", {})
        if isinstance(source_metadata, dict):
            return source_metadata
    return {}


def _deterministic_label(row: dict[str, Any]) -> str | None:
    source_metadata = _metadata_source(row)
    label = _normalize_sentiment_label(str(source_metadata.get("sentiment", "")))
    if label == "unknown":
        return None
    return label


def _deterministic_signed_score(row: dict[str, Any]) -> float | None:
    source_metadata = _metadata_source(row)
    value = source_metadata.get("signed_score")
    if value is None:
        value = source_metadata.get("score")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _top_label_rows(model_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(model_dir.glob("*_scores.jsonl")):
        rows.extend(row for row in _read_jsonl(path) if int(row.get("rank", 0) or 0) == 1)
    return rows


def _collect_similarity_highlights(model_dir: Path) -> list[dict[str, Any]]:
    highlights: list[dict[str, Any]] = []
    for path in sorted(model_dir.glob("*_similarity.json")):
        payload = _read_json(path)
        if payload.get("mode") == "within_case":
            for item in payload.get("neighbors", [])[:3]:
                highlights.append(
                    {
                        "unit_type": payload.get("unit_type"),
                        "source_id": item.get("source_id"),
                        "text": item.get("text"),
                        "nearest_neighbors": item.get("nearest_neighbors", []),
                    }
                )
        elif payload.get("mode") == "prior_guidance_comparison":
            highlights.extend(payload.get("pairs", [])[:5])
    return highlights[:10]


def _classifier_sidecar_comparison(models: dict[str, Any]) -> dict[str, Any]:
    finbert_rows = {
        (row.get("unit_type"), row.get("source_id")): row
        for row in models.get("finbert_tone", {}).get("top_rows", [])
    }
    roberta_rows = {
        (row.get("unit_type"), row.get("source_id")): row
        for row in models.get("financial_roberta", {}).get("top_rows", [])
    }
    comparable_keys = sorted(set(finbert_rows) & set(roberta_rows))
    disagreement_hotspots: list[dict[str, Any]] = []
    agreement_count = 0
    for key in comparable_keys:
        finbert = finbert_rows[key]
        roberta = roberta_rows[key]
        finbert_label = _normalize_sentiment_label(str(finbert.get("label")))
        roberta_label = _normalize_sentiment_label(str(roberta.get("label")))
        if finbert_label == roberta_label:
            agreement_count += 1
            continue
        disagreement_hotspots.append(
            {
                "case_id": finbert.get("case_id"),
                "unit_type": finbert.get("unit_type"),
                "unit_id": finbert.get("source_id"),
                "section": finbert.get("section"),
                "speaker": finbert.get("speaker"),
                "finbert_label": finbert.get("label"),
                "finbert_score": finbert.get("score"),
                "financial_roberta_label": roberta.get("label"),
                "financial_roberta_score": roberta.get("score"),
                "text": str(finbert.get("text", ""))[:320],
                "disagreement_severity": round(
                    max(
                        float(finbert.get("score", 0.0) or 0.0),
                        float(roberta.get("score", 0.0) or 0.0),
                    ),
                    6,
                ),
            }
        )

    disagreement_hotspots = sorted(
        disagreement_hotspots,
        key=lambda row: float(row.get("disagreement_severity", 0.0) or 0.0),
        reverse=True,
    )[:10]
    return {
        "comparable_rows": len(comparable_keys),
        "agreement_rows": agreement_count,
        "disagreement_rows": len(disagreement_hotspots),
        "agreement_rate": round(agreement_count / len(comparable_keys), 4)
        if comparable_keys
        else 0.0,
        "hotspots": disagreement_hotspots,
    }


def _deterministic_comparison(models: dict[str, Any]) -> dict[str, Any]:
    by_model: dict[str, Any] = {}
    hotspots: list[dict[str, Any]] = []
    for model_name in ("finbert_tone", "financial_roberta"):
        rows = models.get(model_name, {}).get("top_rows", [])
        comparable_rows = 0
        agreement_rows = 0
        for row in rows:
            deterministic_label = _deterministic_label(row)
            if row.get("unit_type") != "chunks" or deterministic_label is None:
                continue
            comparable_rows += 1
            sidecar_label = _normalize_sentiment_label(str(row.get("label")))
            if deterministic_label == sidecar_label:
                agreement_rows += 1
                continue
            deterministic_score = _deterministic_signed_score(row)
            sidecar_score = float(row.get("score", 0.0) or 0.0)
            hotspots.append(
                {
                    "case_id": row.get("case_id"),
                    "unit_type": row.get("unit_type"),
                    "unit_id": row.get("source_id"),
                    "text": str(row.get("text", ""))[:320],
                    "deterministic_label": deterministic_label,
                    "deterministic_signal": "chunk_sentiment",
                    "deterministic_score": deterministic_score,
                    "model_name": model_name,
                    "sidecar_label": row.get("label"),
                    "sidecar_score": sidecar_score,
                    "disagreement_severity": round(
                        abs(float(deterministic_score or 0.0)) + abs(sidecar_score),
                        6,
                    ),
                }
            )

        disagreement_rows = comparable_rows - agreement_rows
        by_model[model_name] = {
            "comparable_rows": comparable_rows,
            "agreement_rows": agreement_rows,
            "disagreement_rows": disagreement_rows,
            "agreement_rate": round(agreement_rows / comparable_rows, 4)
            if comparable_rows
            else 0.0,
        }

    hotspots = sorted(
        hotspots,
        key=lambda row: float(row.get("disagreement_severity", 0.0) or 0.0),
        reverse=True,
    )[:10]
    return {"by_model": by_model, "hotspots": hotspots}


def evaluate_case_sidecars(
    case_id: str,
    *,
    sidecar_root: str | Path | None = None,
) -> dict[str, Any]:
    case_output_dir = build_case_sidecar_output_dir(case_id, output_dir=sidecar_root)
    if not case_output_dir.exists():
        raise RuntimeError(
            f"Model-sidecar output directory was not found for case '{case_id}': {case_output_dir}"
        )

    models: dict[str, Any] = {}
    for model_name in AVAILABLE_MODEL_NAMES:
        model_dir = case_output_dir / model_name
        if not model_dir.exists():
            continue
        summary_path = model_dir / "run_summary.json"
        summary = _read_json(summary_path) if summary_path.exists() else {}
        models[model_name] = {
            "runtime_s": summary.get("runtime_s", 0.0),
            "coverage_counts": summary.get("unit_counts", {}),
            "label_distributions": summary.get("label_distributions", {}),
            "vector_dimensions": summary.get("vector_dimensions", {}),
            "top_rows": _top_label_rows(model_dir),
            "similarity_highlights": _collect_similarity_highlights(model_dir),
        }

    sidecar_comparison = _classifier_sidecar_comparison(models)
    deterministic_comparison = _deterministic_comparison(models)
    mpnet_highlights = models.get("mpnet_embeddings", {}).get("similarity_highlights", [])
    report = {
        "case_id": case_id,
        "model_count": len(models),
        "models": {
            model_name: {
                "runtime_s": payload["runtime_s"],
                "coverage_counts": payload["coverage_counts"],
                "label_distributions": payload["label_distributions"],
                "vector_dimensions": payload["vector_dimensions"],
            }
            for model_name, payload in models.items()
        },
        "finbert_vs_financial_roberta": {
            "comparable_rows": sidecar_comparison["comparable_rows"],
            "agreement_rows": sidecar_comparison["agreement_rows"],
            "disagreement_rows": sidecar_comparison["disagreement_rows"],
            "agreement_rate": sidecar_comparison["agreement_rate"],
        },
        "disagreement_hotspots": sidecar_comparison["hotspots"],
        "deterministic_comparison": deterministic_comparison,
        "mpnet_similarity_highlights": mpnet_highlights[:10],
        "incremental_value_summary": {
            "agreement_note": (
                "Use FinBERT-Tone and Financial-RoBERTa agreement as a consistency check, "
                "not as a replacement for deterministic evidence."
            ),
            "deterministic_note": (
                "Use deterministic-vs-sidecar disagreements as an inspection queue only. "
                "These are not accuracy claims."
            ),
            "embedding_note": (
                "Use MPNet neighbors to spot repeated themes or guidance echoes; do not treat "
                "semantic proximity as a trading signal."
            ),
        },
    }
    return report


def render_evaluation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Model Sidecars Evaluation: {payload['case_id']}",
        "",
        "## Coverage And Runtime",
    ]
    for model_name, model_payload in payload.get("models", {}).items():
        lines.append(
            f"- `{model_name}`: runtime `{model_payload.get('runtime_s', 0.0)}`s, "
            f"coverage `{model_payload.get('coverage_counts', {})}`"
        )
    lines.extend(
        [
            "",
            "## Sidecar Agreement",
            (
                "- FinBERT-Tone vs Financial-RoBERTa: "
                f"{payload['finbert_vs_financial_roberta'].get('agreement_rows', 0)} agreement rows, "
                f"{payload['finbert_vs_financial_roberta'].get('disagreement_rows', 0)} disagreements, "
                f"agreement rate `{payload['finbert_vs_financial_roberta'].get('agreement_rate', 0.0)}`"
            ),
            "",
            "## Sidecar Disagreement Hotspots",
        ]
    )
    if payload.get("disagreement_hotspots"):
        for row in payload["disagreement_hotspots"]:
            lines.append(
                "- "
                f"{row.get('unit_type')} / {row.get('unit_id')}: "
                f"FinBERT=`{row.get('finbert_label')}` vs Financial-RoBERTa=`{row.get('financial_roberta_label')}` "
                f"(severity `{row.get('disagreement_severity')}`)"
            )
    else:
        lines.append("- No comparable disagreement hotspots were found.")

    lines.extend(["", "## Deterministic Comparison"])
    for model_name, summary in payload.get("deterministic_comparison", {}).get("by_model", {}).items():
        lines.append(
            "- "
            f"`{model_name}`: {summary.get('agreement_rows', 0)} agreement rows, "
            f"{summary.get('disagreement_rows', 0)} disagreements, "
            f"agreement rate `{summary.get('agreement_rate', 0.0)}`"
        )
    deterministic_hotspots = payload.get("deterministic_comparison", {}).get("hotspots", [])
    if deterministic_hotspots:
        lines.append("")
        lines.append("### Deterministic Hotspots")
        for row in deterministic_hotspots[:5]:
            lines.append(
                "- "
                f"{row.get('model_name')} / {row.get('unit_id')}: "
                f"deterministic=`{row.get('deterministic_label')}` vs sidecar=`{row.get('sidecar_label')}` "
                f"(severity `{row.get('disagreement_severity')}`)"
            )
    else:
        lines.append("- No deterministic comparison hotspots were found.")

    lines.extend(["", "## MPNet Similarity"])
    if payload.get("mpnet_similarity_highlights"):
        for row in payload["mpnet_similarity_highlights"][:5]:
            if "nearest_neighbors" in row:
                lines.append(
                    "- "
                    f"{row.get('unit_type')} / {row.get('source_id')}: "
                    f"{len(row.get('nearest_neighbors', []))} nearest-neighbor matches saved."
                )
            else:
                lines.append(
                    "- "
                    f"{row.get('topic', 'guidance')} / {row.get('period', 'unknown')}: "
                    f"similarity `{row.get('similarity', 0.0)}`"
                )
    else:
        lines.append("- No MPNet similarity outputs were found.")

    lines.extend(
        [
            "",
            "## Incremental Value Scaffold",
            f"- {payload['incremental_value_summary']['agreement_note']}",
            f"- {payload['incremental_value_summary']['deterministic_note']}",
            f"- {payload['incremental_value_summary']['embedding_note']}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_evaluation_outputs(
    case_id: str,
    *,
    sidecar_root: str | Path | None = None,
) -> dict[str, Path]:
    case_output_dir = build_case_sidecar_output_dir(case_id, output_dir=sidecar_root)
    payload = evaluate_case_sidecars(case_id, sidecar_root=sidecar_root)
    json_path = case_output_dir / "model_sidecars_evaluation.json"
    md_path = case_output_dir / "model_sidecars_evaluation.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_evaluation_markdown(payload), encoding="utf-8")
    return {"json_path": json_path, "md_path": md_path}
