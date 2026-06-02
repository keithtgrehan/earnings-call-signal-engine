from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

import pytest
import yaml

from signal_engine.retrieval.object_metadata import build_retrieval_object_metadata
from signal_engine.retrieval.providers.config import ALLOWED_PROVIDER_SLOTS, load_provider_config, validate_provider_config_payload
from signal_engine.retrieval.providers.safety import (
    RETRIEVAL_PROVIDER_STATUS_LABEL,
    validate_provider_output_payload,
    validate_safe_provider_output_path,
)
from tools.run_retrieval_provider_dry_run import main as provider_dry_run_cli
from tools.run_retrieval_provider_dry_run import run_provider_dry_run


def _metadata_row(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "object_type": "evidence_object_metadata",
        "case_id": "hd_2025_q4",
        "company": "The Home Depot, Inc.",
        "ticker": "HD",
        "fiscal_period": "2025 Q4",
        "source_type": "manual_local_transcript_evidence",
        "provenance_ref": "/safe/provenance/normalized_transcript.json",
        "source_hash": "sha256:" + "a" * 64,
        "text_hash": "sha256:" + "b" * 64,
        "normalized_transcript_hash": "sha256:" + "c" * 64,
        "provenance_hash": "sha256:" + "d" * 64,
        "section_label": "prepared_remarks",
        "speaker_role": "management",
        "topic": "guidance",
        "span_start_char": 10,
        "span_end_char": 20,
        "rights_tier": "safe_to_download",
    }
    values.update(overrides)
    return build_retrieval_object_metadata(**values)  # type: ignore[arg-type]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _example_config_payload() -> dict[str, Any]:
    return yaml.safe_load(Path("configs/retrieval_providers.example.yml").read_text(encoding="utf-8"))


def _write_config(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_retrieval_provider_config_schema_is_fail_closed() -> None:
    schema = json.loads(Path("schemas/retrieval_provider_config.schema.json").read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["properties"]["default_provider"]["const"] == "local_stub"
    assert schema["properties"]["network_enabled"]["const"] is False
    assert set(schema["properties"]["providers"]["required"]) == set(ALLOWED_PROVIDER_SLOTS)
    assert schema["properties"]["providers"]["additionalProperties"] is False
    assert schema["$defs"]["local_stub"]["properties"]["enabled"]["const"] is True
    assert schema["$defs"]["disabled_real_provider"]["properties"]["enabled"]["const"] is False


def test_example_provider_config_validates_and_uses_local_stub() -> None:
    config = load_provider_config(Path("configs/retrieval_providers.example.yml"))

    assert config.status_label == RETRIEVAL_PROVIDER_STATUS_LABEL
    assert config.default_provider == "local_stub"
    assert config.network_enabled is False
    assert config.default_slot.enabled is True
    assert config.default_slot.mode == "dry_run"
    assert all(not provider.enabled for slot, provider in config.providers.items() if slot != "local_stub")


def test_unknown_provider_rejected() -> None:
    payload = _example_config_payload()
    payload["providers"]["unknown_embedding"] = {
        "provider_type": "unknown_embedding",
        "enabled": False,
        "mode": "disabled",
        "network_enabled": False,
        "model": "placeholder",
        "api_key_env": "UNKNOWN_API_KEY",
    }

    errors = validate_provider_config_payload(payload)

    assert any("unknown provider slot unknown_embedding" in error for error in errors)


def test_missing_required_provider_fields_rejected() -> None:
    payload = _example_config_payload()
    del payload["providers"]["openai_embedding"]["api_key_env"]

    errors = validate_provider_config_payload(payload)

    assert any("provider openai_embedding missing required field api_key_env" in error for error in errors)


def test_enabled_real_provider_rejected() -> None:
    payload = _example_config_payload()
    payload["providers"]["openai_embedding"]["enabled"] = True

    errors = validate_provider_config_payload(payload)

    assert any("provider openai_embedding must remain disabled" in error for error in errors)


def test_default_local_stub_dry_run_succeeds_without_api_keys_or_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in ("OPENAI_API_KEY", "VOYAGE_API_KEY", "COHERE_API_KEY", "JINA_API_KEY"):
        monkeypatch.delenv(env_name, raising=False)

    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("network calls are not allowed in provider dry-run tests")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    objects_path = tmp_path / "objects.jsonl"
    _write_jsonl(objects_path, [_metadata_row()])

    payload = run_provider_dry_run(
        config_path=Path("configs/retrieval_providers.example.yml"),
        objects_path=objects_path,
        json_out=tmp_path / "dry_run.json",
        markdown_out=tmp_path / "dry_run.md",
        dry_run=True,
    )

    assert payload["status_label"] == RETRIEVAL_PROVIDER_STATUS_LABEL
    assert payload["provider_slot"] == "local_stub"
    assert payload["object_count"] == 1
    assert payload["network_calls"] is False
    assert payload["embeddings_generated"] is False
    assert payload["vector_db_generated"] is False
    assert payload["provider_benchmark_complete"] is False
    assert payload["evaluated_retrieval_quality"] is False


def test_dry_run_cli_requires_dry_run_flag(tmp_path: Path) -> None:
    objects_path = tmp_path / "objects.jsonl"
    _write_jsonl(objects_path, [_metadata_row()])

    exit_code = provider_dry_run_cli(
        [
            "--config",
            "configs/retrieval_providers.example.yml",
            "--objects",
            str(objects_path),
            "--json-out",
            str(tmp_path / "dry_run.json"),
            "--report",
            str(tmp_path / "dry_run.md"),
        ]
    )

    assert exit_code == 1


def test_restricted_output_path_blocked(tmp_path: Path) -> None:
    errors = validate_safe_provider_output_path(tmp_path / "raw" / "dry_run.json")

    assert any("restricted component" in error for error in errors)


@pytest.mark.parametrize("filename", ["embedding_report.json", "vector_report.json", "index_report.json", "faiss_report.md", "chroma_report.md", "lancedb_report.json"])
def test_embedding_vector_index_output_names_blocked(tmp_path: Path, filename: str) -> None:
    errors = validate_safe_provider_output_path(tmp_path / filename)

    assert any("filename suggests" in error for error in errors)


def test_dry_run_metadata_is_deterministic(tmp_path: Path) -> None:
    objects_path = tmp_path / "objects.jsonl"
    _write_jsonl(objects_path, [_metadata_row(), _metadata_row(case_id="hd_2024_q4", text_hash="sha256:" + "e" * 64)])

    first = run_provider_dry_run(
        config_path=Path("configs/retrieval_providers.example.yml"),
        objects_path=objects_path,
        json_out=tmp_path / "first.json",
        markdown_out=tmp_path / "first.md",
        dry_run=True,
    )
    second = run_provider_dry_run(
        config_path=Path("configs/retrieval_providers.example.yml"),
        objects_path=objects_path,
        json_out=tmp_path / "second.json",
        markdown_out=tmp_path / "second.md",
        dry_run=True,
    )

    assert first == second
    assert first["object_metadata_digest"].startswith("sha256:")
    first_json = (tmp_path / "first.json").read_text(encoding="utf-8")
    assert '"embeddings":' not in first_json
    assert '"vectors":' not in first_json


def test_raw_text_like_provider_output_rejected() -> None:
    errors = validate_provider_output_payload({"rawTranscriptText": "blocked"})

    assert any("forbidden" in error for error in errors)


def test_provider_dry_run_validates_input_metadata(tmp_path: Path) -> None:
    objects_path = tmp_path / "objects.jsonl"
    row = _metadata_row()
    row["provenance_ref"] = ""
    _write_jsonl(objects_path, [row])

    with pytest.raises(ValueError, match="provenance_ref"):
        run_provider_dry_run(
            config_path=Path("configs/retrieval_providers.example.yml"),
            objects_path=objects_path,
            json_out=tmp_path / "dry_run.json",
            markdown_out=tmp_path / "dry_run.md",
            dry_run=True,
        )


def test_deterministic_extraction_modules_do_not_import_provider_layer() -> None:
    deterministic_paths = [
        Path("src/signal_engine/agent1_extraction.py"),
        Path("src/signal_engine/first30_extraction/extractor.py"),
        *sorted(Path("src/earnings_call_sentiment/signals").glob("*.py")),
    ]

    for path in deterministic_paths:
        assert "retrieval.providers" not in path.read_text(encoding="utf-8")
