#!/usr/bin/env python3
"""Run a metadata-only retrieval provider dry run without APIs, embeddings, or vector DBs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval.object_metadata import validate_retrieval_object_metadata_rows  # noqa: E402
from signal_engine.retrieval.providers.config import load_provider_config  # noqa: E402
from signal_engine.retrieval.providers.safety import validate_provider_report_payload, validate_safe_provider_output_path  # noqa: E402
from signal_engine.retrieval.providers.stubs import DryRunEmbeddingProvider  # noqa: E402

DEFAULT_CONFIG = ROOT / "configs" / "retrieval_providers.example.yml"
DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_object_metadata.jsonl"


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Provider Dry Run",
        "",
        "## Run status",
        f"- status: `{payload['status_label']}`",
        f"- evaluated retrieval quality: `{str(payload['evaluated_retrieval_quality']).lower()}`",
        f"- embeddings generated: `{str(payload['embeddings_generated']).lower()}`",
        f"- vector DB generated: `{str(payload['vector_db_generated']).lower()}`",
        f"- network calls: `{str(payload['network_calls']).lower()}`",
        f"- provider benchmark complete: `{str(payload['provider_benchmark_complete']).lower()}`",
        f"- production RAG claim: `{str(payload['production_rag_claim']).lower()}`",
        "",
        "## Provider",
        f"- provider slot: `{payload['provider_slot']}`",
        f"- provider type: `{payload['provider_type']}`",
        f"- provider mode: `{payload['provider_mode']}`",
        "- local_stub is the only enabled provider in this scaffold.",
        "- External embedding and reranking providers are represented as disabled slots only.",
        "",
        "## Inputs",
        f"- config path: `{payload['config_path']}`",
        f"- objects path: `{payload['objects_path']}`",
        f"- metadata object count: `{payload['object_count']}`",
        f"- metadata object digest: `{payload['object_metadata_digest']}`",
        "",
        "## Counts by object type",
    ]
    for object_type, count in payload["counts_by_object_type"].items():
        lines.append(f"- {object_type}: `{count}`")
    lines.extend(["", "## Counts by case_id"])
    for case_id, count in payload["counts_by_case_id"].items():
        lines.append(f"- {case_id}: `{count}`")
    lines.extend(
        [
            "",
            "## Safety",
            "- This report contains metadata-only run metadata.",
            "- No raw transcript text, ASR/audio text, chunk body text, provider response payloads, embeddings, vectors, indexes, or vector DB files are produced.",
            "- This is adapter foundation only and does not benchmark provider quality.",
            "- Later bakeoffs must use reviewed retrieval eval queries, explicit non-committed provider config, safe output locations, and artifact scans before metrics are interpreted.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_provider_dry_run(
    *,
    config_path: Path = DEFAULT_CONFIG,
    objects_path: Path = DEFAULT_OBJECTS,
    json_out: Path | None = None,
    markdown_out: Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("only --dry-run mode is supported; provider execution is not enabled")

    config = load_provider_config(_repo_path(config_path))
    resolved_objects_path = _repo_path(objects_path)
    rows = read_jsonl(resolved_objects_path)
    object_errors = validate_retrieval_object_metadata_rows(rows)
    if object_errors:
        raise ValueError("; ".join(object_errors))

    json_report = _repo_path(json_out or Path(config.outputs["json_report"]))
    markdown_report = _repo_path(markdown_out or Path(config.outputs["markdown_report"]))
    path_errors = []
    for path in (json_report, markdown_report):
        path_errors.extend(f"{_display_path(path)}: {error}" for error in validate_safe_provider_output_path(path))
    if path_errors:
        raise ValueError("; ".join(path_errors))

    provider = DryRunEmbeddingProvider(config.default_slot)
    payload = provider.dry_run_metadata(
        rows,
        config_path=_display_path(_repo_path(config_path)),
        objects_path=_display_path(resolved_objects_path),
    ).to_dict()
    report_errors = validate_provider_report_payload(payload)
    if report_errors:
        raise ValueError("; ".join(report_errors))

    write_json(json_report, payload)
    write_markdown_report(markdown_report, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a metadata-only retrieval provider dry run.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Required. No provider APIs, embeddings, or vector DBs are created.")
    args = parser.parse_args(argv)
    try:
        payload = run_provider_dry_run(
            config_path=args.config,
            objects_path=args.objects,
            json_out=args.json_out,
            markdown_out=args.report,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"Retrieval provider dry run blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
