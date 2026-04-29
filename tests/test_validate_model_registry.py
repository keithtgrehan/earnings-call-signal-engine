from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_model_registry.py"
EXPECTED_MODEL_IDS = {
    "deterministic_rules_baseline",
    "weak_label_keyword_baseline",
    "local_sklearn_text_classifier",
    "sentence_transformers_local_candidate",
    "openai_text_embedding_3_large_candidate",
    "voyage_embedding_candidate",
    "cohere_embed_candidate",
    "jina_embedding_candidate",
    "cohere_rerank_candidate",
    "jina_reranker_candidate",
    "openai_long_context_candidate",
    "anthropic_long_context_candidate",
    "google_long_context_candidate",
}


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_valid_model_registry_passes_and_tracks_expected_ids() -> None:
    result = run_validator("--path", "data/model_registry.example.json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads((ROOT / "data/model_registry.example.json").read_text(encoding="utf-8"))
    assert {row["model_id"] for row in payload["models"]} == EXPECTED_MODEL_IDS
    assert all(row["model_weights_committed"] is False for row in payload["models"])
    assert all(row["validated"] is False for row in payload["models"])


def test_missing_required_model_field_fails(tmp_path: Path) -> None:
    broken = {
        "models": [
            {
                "model_name": "Broken",
                "model_type": "candidate",
                "status": "planned",
                "intended_use": "test",
                "requires_external_api": False,
                "requires_local_download": False,
                "model_weights_committed": False,
                "validated": False,
                "notes": "missing model_id",
            }
        ]
    }
    path = tmp_path / "broken_model_registry.json"
    path.write_text(json.dumps(broken), encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "missing required field model_id" in result.stdout


def test_committed_model_weights_fail(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "data/model_registry.example.json").read_text(encoding="utf-8"))
    payload["models"][0]["model_weights_committed"] = True
    path = tmp_path / "weights_committed.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "model_weights_committed must be false" in result.stdout
