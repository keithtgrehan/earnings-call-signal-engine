"""Benchmark report helpers for optional model sidecars."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import benchmark_json_path, benchmark_markdown_path


def _case_lookup(payload: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case_payload in payload.get("cases", []):
        if case_payload.get("case_id") == case_id:
            return case_payload
    raise RuntimeError(f"Benchmark payload did not include case '{case_id}'.")


def build_case_benchmark_report(payload: dict[str, Any], case_id: str) -> dict[str, Any]:
    benchmark_runs: list[dict[str, Any]] = []
    case_output_root: str | None = None
    for run in payload.get("runs", []):
        case_payload = _case_lookup(run["payload"], case_id)
        case_output_root = case_payload.get("output_root", case_output_root)
        benchmark_runs.append(
            {
                "run_label": run["run_label"],
                "models": case_payload.get("models", {}),
                "sampling": case_payload.get("sampling", {}),
            }
        )

    return {
        "case_id": case_id,
        "output_root": case_output_root,
        "run_mode": payload.get("run_mode"),
        "benchmark_runs": benchmark_runs,
        "notes": payload.get("notes", []),
    }


def render_benchmark_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Model Sidecars Benchmark: {payload['case_id']}",
        "",
        "This report summarizes optional sidecar runtime behavior only.",
        "Deterministic transcript-first outputs remain the source of truth.",
    ]
    for run in payload.get("benchmark_runs", []):
        lines.extend(["", f"## {run['run_label'].title()} Run"])
        for model_name, model_payload in run.get("models", {}).items():
            lines.append(
                "- "
                f"`{model_name}`: runtime `{model_payload.get('runtime_s', 0.0)}`s, "
                f"prewarm `{model_payload.get('prewarm_runtime_s', 0.0)}`s, "
                f"device `{model_payload.get('device', 'unknown')}`"
            )
            for unit_type, unit_payload in model_payload.get("unit_results", {}).items():
                lines.append(
                    "  "
                    f"- `{unit_type}`: {unit_payload.get('selected_count', 0)} items, "
                    f"`{unit_payload.get('runtime_s', 0.0)}`s, "
                    f"`{unit_payload.get('items_per_s')}` items/s, "
                    f"peak RSS `{unit_payload.get('process_peak_rss_bytes')}`"
                )
    if payload.get("notes"):
        lines.extend(["", "## Notes"])
        for note in payload["notes"]:
            lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def write_benchmark_outputs(
    payload: dict[str, Any],
    *,
    output_root: str | Path | None = None,
) -> dict[str, dict[str, Path]]:
    artifacts: dict[str, dict[str, Path]] = {}
    case_ids: list[str] = []
    for run in payload.get("runs", []):
        for case_payload in run.get("payload", {}).get("cases", []):
            case_id = str(case_payload.get("case_id"))
            if case_id not in case_ids:
                case_ids.append(case_id)

    for case_id in case_ids:
        case_report = build_case_benchmark_report(payload, case_id)
        json_path = benchmark_json_path(case_id, output_root=output_root)
        md_path = benchmark_markdown_path(case_id, output_root=output_root)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(case_report, indent=2), encoding="utf-8")
        md_path.write_text(render_benchmark_markdown(case_report), encoding="utf-8")
        artifacts[case_id] = {"json_path": json_path, "md_path": md_path}
    return artifacts
