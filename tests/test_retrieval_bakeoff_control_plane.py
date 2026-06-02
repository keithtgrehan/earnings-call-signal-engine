from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from signal_engine.retrieval.bakeoff import (
    BAKEOFF_STATUS_LABEL,
    SUPPORTED_BAKEOFF_METRICS,
    load_bakeoff_manifest,
    validate_bakeoff_manifest_payload,
    validate_bakeoff_output_root,
)
from tools.plan_retrieval_bakeoff import main as plan_bakeoff_cli
from tools.plan_retrieval_bakeoff import plan_retrieval_bakeoff
from tools.validate_retrieval_bakeoff_manifest import main as validate_bakeoff_cli


ROOT = Path(".")


def _example_manifest() -> dict[str, Any]:
    return yaml.safe_load(Path("configs/retrieval_bakeoff.example.yml").read_text(encoding="utf-8"))


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_retrieval_bakeoff_manifest_schema_is_plan_only() -> None:
    schema = json.loads(Path("schemas/retrieval_bakeoff_manifest.schema.json").read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["properties"]["status_label"]["const"] == BAKEOFF_STATUS_LABEL
    assert schema["properties"]["network_allowed"]["const"] is False
    assert set(schema["properties"]["provider_slots"]["items"]["enum"]) == {
        "local_stub",
        "openai_embedding",
        "voyage_embedding",
        "cohere_embedding",
        "jina_embedding",
        "cohere_rerank",
        "jina_rerank",
    }


def test_valid_example_manifest() -> None:
    manifest = load_bakeoff_manifest(Path("configs/retrieval_bakeoff.example.yml"), root=ROOT)

    assert manifest.payload["status_label"] == BAKEOFF_STATUS_LABEL
    assert manifest.payload["provider_slots"] == ["local_stub"]
    assert manifest.payload["network_allowed"] is False
    assert manifest.payload["reviewed_query_set"]["smoke_only"] is True


def test_validate_bakeoff_manifest_cli_accepts_example() -> None:
    exit_code = validate_bakeoff_cli(["--manifest", "configs/retrieval_bakeoff.example.yml"])

    assert exit_code == 0


def test_unknown_provider_rejected() -> None:
    payload = _example_manifest()
    payload["provider_slots"] = ["unknown_provider"]

    errors = validate_bakeoff_manifest_payload(payload, root=ROOT)

    assert any("unknown provider slot unknown_provider" in error for error in errors)


def test_network_disabled_real_provider_rejected() -> None:
    payload = _example_manifest()
    payload["provider_slots"] = ["openai_embedding"]

    errors = validate_bakeoff_manifest_payload(payload, root=ROOT)

    assert any("real provider slot openai_embedding" in error for error in errors)


def test_restricted_output_path_rejected() -> None:
    errors = validate_bakeoff_output_root(Path("reports/retrieval"), root=ROOT)

    assert any("restricted component" in error or ".local" in error for error in errors)


def test_embedding_vector_index_output_root_rejected() -> None:
    errors = validate_bakeoff_output_root(Path("/tmp/signal-engine-retrieval-bakeoffs/vector_index_run"), root=ROOT)

    assert any("embeddings, vectors, indexes" in error for error in errors)


def test_unsupported_metric_rejected() -> None:
    payload = _example_manifest()
    payload["metrics_planned"] = sorted(SUPPORTED_BAKEOFF_METRICS) + ["provider_win_rate"]

    errors = validate_bakeoff_manifest_payload(payload, root=ROOT)

    assert any("unsupported metric provider_win_rate" in error for error in errors)


def test_overclaiming_status_rejected() -> None:
    payload = _example_manifest()
    payload["status_label"] = "retrieval_bakeoff_benchmarked"

    errors = validate_bakeoff_manifest_payload(payload, root=ROOT)

    assert any("status_label" in error for error in errors)


def test_missing_reviewed_query_gate_rejected() -> None:
    payload = _example_manifest()
    payload["reviewed_query_set"]["reviewed"] = False
    payload["reviewed_query_set"]["smoke_only"] = False

    errors = validate_bakeoff_manifest_payload(payload, root=ROOT)

    assert any("unreviewed query sets" in error for error in errors)


def test_smoke_only_plan_produces_scaffold_only_status(tmp_path: Path) -> None:
    payload = _example_manifest()
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "bakeoff_plan.json"),
        "markdown_report": str(tmp_path / "bakeoff_plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    summary = plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)

    assert summary["status_label"] == BAKEOFF_STATUS_LABEL
    assert summary["smoke_only"] is True
    assert summary["reviewed_query_set"] is False
    assert summary["real_benchmark_allowed"] is False
    assert summary["network_calls"] is False
    assert summary["embeddings_generated"] is False
    assert summary["vector_db_generated"] is False
    assert summary["benchmark_complete"] is False
    assert summary["evaluated_retrieval_quality"] is False


def test_plan_cli_requires_dry_run(tmp_path: Path) -> None:
    payload = _example_manifest()
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "bakeoff_plan.json"),
        "markdown_report": str(tmp_path / "bakeoff_plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    exit_code = plan_bakeoff_cli(["--manifest", str(manifest_path)])

    assert exit_code == 1


def test_dry_run_plan_deterministic_output(tmp_path: Path) -> None:
    payload = _example_manifest()
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "first.json"),
        "markdown_report": str(tmp_path / "first.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    first = plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)
    second = plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)

    assert first == second
    assert first["object_metadata_digest"].startswith("sha256:")
    assert first["query_set_digest"].startswith("sha256:")


def test_raw_text_fields_rejected_in_query_set(tmp_path: Path) -> None:
    query = json.loads(Path("data/retrieval/eval_queries_hd_2025_q4.jsonl").read_text(encoding="utf-8").splitlines()[0])
    query["raw_text"] = "blocked"
    query_path = tmp_path / "queries.jsonl"
    query_path.write_text(json.dumps(query, sort_keys=True) + "\n", encoding="utf-8")
    payload = _example_manifest()
    payload["reviewed_query_set"]["path"] = str(query_path)
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "plan.json"),
        "markdown_report": str(tmp_path / "plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    with pytest.raises(ValueError, match="raw_text|forbidden"):
        plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)


def test_no_raw_text_fields_in_reports_json(tmp_path: Path) -> None:
    payload = _example_manifest()
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "bakeoff_plan.json"),
        "markdown_report": str(tmp_path / "bakeoff_plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)
    report_json = (tmp_path / "bakeoff_plan.json").read_text(encoding="utf-8")
    report_md = (tmp_path / "bakeoff_plan.md").read_text(encoding="utf-8")

    assert '"raw_text"' not in report_json
    assert '"chunk_text"' not in report_json
    assert '"provider_response"' not in report_json
    assert '"vectors":' not in report_json
    assert '"embeddings":' not in report_json
    assert "planned_metrics" not in report_md.lower()


def test_no_generated_embeddings_or_vector_db_files_created(tmp_path: Path) -> None:
    payload = _example_manifest()
    output_root = Path("/tmp/signal-engine-r6-safe-local-bakeoff")
    payload["output_root"] = str(output_root)
    payload["plan_outputs"] = {
        "json_report": str(tmp_path / "bakeoff_plan.json"),
        "markdown_report": str(tmp_path / "bakeoff_plan.md"),
    }
    manifest_path = tmp_path / "manifest.yml"
    _write_manifest(manifest_path, payload)

    plan_retrieval_bakeoff(manifest_path=manifest_path, dry_run=True)

    generated_names = [path.name for path in tmp_path.rglob("*")]
    assert not any(name.endswith((".npy", ".npz", ".faiss", ".index", ".sqlite", ".db")) for name in generated_names)
    assert not output_root.exists()
