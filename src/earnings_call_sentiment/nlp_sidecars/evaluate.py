"""Comparison and disagreement summaries for optional NLP sidecars."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .base import ClassificationResult, EmbeddingResult, normalize_polarity_label
from .io import evaluation_output_dir, model_output_dir


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _normalize_label_for_compare(value: Any) -> str:
    return str(value or "").strip().casefold()


def build_classification_disagreement_report(
    *,
    model_name: str,
    results: list[ClassificationResult],
) -> dict[str, Any]:
    if not results:
        return {
            "status": "no_rows",
            "model_name": model_name,
            "notes": [
                "No optional sidecar rows were available.",
                "Deterministic outputs remain the source of truth.",
            ],
        }

    rows = []
    for result in results:
        top = result.scores[0] if result.scores else None
        rows.append(
            {
                "unit_type": result.unit.unit_type,
                "unit_id": result.unit.unit_id,
                "top_label": top.label if top else "",
                "top_score": top.score if top else 0.0,
                "comparable_label": result.comparable_label or "",
                "deterministic_label": result.unit.deterministic_label or "",
                "deterministic_polarity": normalize_polarity_label(result.unit.deterministic_label),
                "text": result.unit.text,
            }
        )
    frame = pd.DataFrame(rows)
    comparable = frame[frame["comparable_label"].astype(str).str.strip() != ""].copy()
    comparable = comparable[comparable["deterministic_polarity"].astype(str).str.strip() != ""].copy()
    comparable["agrees"] = comparable["comparable_label"] == comparable["deterministic_polarity"]
    examples = [
        {
            "unit_id": str(row["unit_id"]),
            "unit_type": str(row["unit_type"]),
            "deterministic_polarity": str(row["deterministic_polarity"]),
            "model_label": str(row["comparable_label"]),
            "top_label": str(row["top_label"]),
            "top_score": round(float(row["top_score"]), 4),
            "text": str(row["text"])[:240],
        }
        for _, row in comparable[~comparable["agrees"]]
        .sort_values(["top_score", "unit_type"], ascending=[False, True])
        .head(8)
        .iterrows()
    ]
    by_unit = {}
    for unit_type, unit_frame in comparable.groupby("unit_type"):
        by_unit[str(unit_type)] = {
            "comparable_rows": int(len(unit_frame)),
            "agreement_rows": int(unit_frame["agrees"].sum()),
            "disagreement_rows": int((~unit_frame["agrees"]).sum()),
        }
    return {
        "status": "ok",
        "model_name": model_name,
        "row_count": int(len(frame)),
        "deterministic_comparison": {
            "comparable_rows": int(len(comparable)),
            "agreement_rows": int(comparable["agrees"].sum()) if not comparable.empty else 0,
            "disagreement_rows": int((~comparable["agrees"]).sum()) if not comparable.empty else 0,
            "agreement_rate": round(float(comparable["agrees"].mean()), 4) if not comparable.empty else 0.0,
            "by_unit_type": by_unit,
            "examples": examples,
        },
        "notes": [
            "Deterministic outputs remain the canonical review truth.",
            "Model disagreement highlights are for inspection only and do not re-label the case.",
        ],
    }


def build_embedding_disagreement_report(
    *,
    model_name: str,
    results: list[EmbeddingResult],
) -> dict[str, Any]:
    if not results:
        return {
            "status": "no_rows",
            "model_name": model_name,
            "notes": [
                "No optional embedding rows were available.",
                "Embeddings are supporting similarity aids only.",
            ],
        }

    rows = []
    for result in results:
        rows.append(
            {
                "unit_id": result.unit.unit_id,
                "unit_type": result.unit.unit_type,
                "deterministic_polarity": normalize_polarity_label(result.unit.deterministic_label),
                "vector": result.vector,
                "text": result.unit.text,
            }
        )

    hotspots: list[dict[str, Any]] = []
    for left, right in itertools.combinations(rows, 2):
        if not left["vector"] or not right["vector"]:
            continue
        similarity = sum(a * b for a, b in zip(left["vector"], right["vector"], strict=True))
        if similarity < 0.75:
            continue
        if (
            left["deterministic_polarity"]
            and right["deterministic_polarity"]
            and left["deterministic_polarity"] != right["deterministic_polarity"]
        ):
            hotspots.append(
                {
                    "left_unit_id": left["unit_id"],
                    "right_unit_id": right["unit_id"],
                    "left_unit_type": left["unit_type"],
                    "right_unit_type": right["unit_type"],
                    "similarity": round(float(similarity), 4),
                    "left_polarity": left["deterministic_polarity"],
                    "right_polarity": right["deterministic_polarity"],
                    "left_text": str(left["text"])[:160],
                    "right_text": str(right["text"])[:160],
                }
            )
    hotspots = sorted(hotspots, key=lambda item: item["similarity"], reverse=True)[:8]
    return {
        "status": "ok",
        "model_name": model_name,
        "row_count": len(results),
        "similarity_hotspots": hotspots,
        "notes": [
            "Embeddings are used here for similarity and disagreement inspection only.",
            "High-similarity rows with different deterministic polarity are review hotspots, not proof of model lift.",
        ],
    }


def build_markdown_summary(
    *,
    model_name: str,
    model_kind: str,
    run_summary: dict[str, Any],
    disagreement_report: dict[str, Any],
) -> str:
    lines = [
        f"# {model_name}",
        "",
        f"- Status: `{run_summary.get('status', 'unknown')}`",
        f"- Output kind: `{model_kind}`",
        f"- Units processed: `{run_summary.get('units_processed', 0)}`",
        f"- Runtime seconds: `{run_summary.get('runtime_s', 0.0)}`",
        f"- Device: `{run_summary.get('device', '')}`",
        "",
        "Notes:",
    ]
    for note in run_summary.get("notes", []):
        lines.append(f"- {note}")
    comparison = disagreement_report.get("deterministic_comparison", {})
    if comparison:
        lines.extend(
            [
                "",
                "Deterministic comparison:",
                f"- Comparable rows: `{comparison.get('comparable_rows', 0)}`",
                f"- Agreement rate: `{comparison.get('agreement_rate', 0.0)}`",
                f"- Disagreement rows: `{comparison.get('disagreement_rows', 0)}`",
            ]
        )
    hotspots = disagreement_report.get("similarity_hotspots", [])
    if hotspots:
        lines.extend(
            [
                "",
                "Similarity hotspots:",
                f"- High-similarity polarity mismatches: `{len(hotspots)}`",
            ]
        )
    return "\n".join(lines) + "\n"


def write_case_evaluation_summary(
    *,
    case_id: str,
    output_root: str | Path | None = None,
) -> dict[str, Path]:
    base_dir = evaluation_output_dir(case_id=case_id, output_root=output_root)
    case_dir = base_dir.parent
    summaries: list[dict[str, Any]] = []
    classification_frames: dict[str, pd.DataFrame] = {}

    for model_dir in sorted(path for path in case_dir.iterdir() if path.is_dir() and path.name != "evaluation"):
        summary_path = model_dir / "run_summary.json"
        rows_path = model_dir / "scored_rows.csv"
        if not summary_path.exists() or not rows_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summaries.append(summary)
        if summary.get("model_kind") == "classification":
            classification_frames[model_dir.name] = pd.read_csv(rows_path, keep_default_na=False)

    pairwise: list[dict[str, Any]] = []
    for left_name, right_name in itertools.combinations(sorted(classification_frames), 2):
        left = classification_frames[left_name]
        right = classification_frames[right_name]
        merged = left.merge(
            right,
            on=["case_id", "unit_type", "unit_id"],
            suffixes=("_left", "_right"),
            how="inner",
        )
        if merged.empty:
            continue
        merged["top_agrees"] = (
            merged["top_label_left"].map(_normalize_label_for_compare)
            == merged["top_label_right"].map(_normalize_label_for_compare)
        )
        comparable = merged[
            (merged["comparable_label_left"].astype(str).str.strip() != "")
            & (merged["comparable_label_right"].astype(str).str.strip() != "")
        ].copy()
        comparable["comparable_agrees"] = (
            comparable["comparable_label_left"].map(_normalize_label_for_compare)
            == comparable["comparable_label_right"].map(_normalize_label_for_compare)
        )
        hotspots = [
            {
                "unit_id": str(row["unit_id"]),
                "unit_type": str(row["unit_type"]),
                "left_top_label": str(row["top_label_left"]),
                "right_top_label": str(row["top_label_right"]),
                "left_top_score": round(float(row["top_score_left"]), 4),
                "right_top_score": round(float(row["top_score_right"]), 4),
                "text": str(row["text_left"])[:220],
            }
            for _, row in merged[~merged["top_agrees"]]
            .sort_values(["top_score_left", "top_score_right"], ascending=[False, False])
            .head(8)
            .iterrows()
        ]
        pairwise.append(
            {
                "left_model": left_name,
                "right_model": right_name,
                "rows_compared": int(len(merged)),
                "top_label_agreement_rate": round(float(merged["top_agrees"].mean()), 4),
                "comparable_label_agreement_rate": (
                    round(float(comparable["comparable_agrees"].mean()), 4)
                    if not comparable.empty
                    else None
                ),
                "hotspots": hotspots,
                "notes": [
                    "Exact top-label agreement can be noisy when label spaces differ.",
                    "Comparable-label agreement uses normalized polarity when both models expose it.",
                ],
            }
        )

    runtime_summary = {
        "case_id": case_id,
        "models": [
            {
                "model_name": item.get("model_name"),
                "status": item.get("status"),
                "model_kind": item.get("model_kind"),
                "runtime_s": item.get("runtime_s"),
                "units_processed": item.get("units_processed"),
                "unit_type_counts": item.get("unit_type_counts", {}),
            }
            for item in summaries
        ],
    }
    comparison_summary = {
        "case_id": case_id,
        "models_covered": [item.get("model_name") for item in summaries],
        "pairwise_classification": pairwise,
        "notes": [
            "These comparisons are additive sidecar diagnostics only.",
            "Deterministic transcript-backed outputs remain canonical.",
        ],
    }

    base_dir.mkdir(parents=True, exist_ok=True)
    runtime_path = base_dir / "runtime_summary.json"
    comparison_path = base_dir / "comparison_summary.json"
    markdown_path = base_dir / "comparison_summary.md"
    runtime_path.write_text(json.dumps(runtime_summary, indent=2), encoding="utf-8")
    comparison_path.write_text(json.dumps(comparison_summary, indent=2), encoding="utf-8")

    lines = [
        f"# NLP Sidecar Evaluation Summary: {case_id}",
        "",
        "Runtime summary:",
    ]
    for item in runtime_summary["models"]:
        lines.append(
            f"- `{item['model_name']}`: status=`{item['status']}`, runtime_s=`{item['runtime_s']}`, units=`{item['units_processed']}`"
        )
    if pairwise:
        lines.extend(["", "Pairwise classification comparisons:"])
        for item in pairwise:
            lines.append(
                f"- `{item['left_model']}` vs `{item['right_model']}`: top_label_agreement_rate=`{item['top_label_agreement_rate']}`, comparable_label_agreement_rate=`{item['comparable_label_agreement_rate']}`"
            )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "runtime_summary": runtime_path,
        "comparison_summary": comparison_path,
        "comparison_markdown": markdown_path,
    }
