from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_nlp_tools_registry.py"


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_valid_nlp_tools_registry_passes_with_required_counts() -> None:
    result = run_validator("--path", "data/nlp_tools_registry.example.json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads((ROOT / "data/nlp_tools_registry.example.json").read_text(encoding="utf-8"))
    rows = payload["tools"]
    counts = Counter(row["category"] for row in rows)
    assert 45 <= len(rows) <= 60
    assert counts["core_nlp"] >= 7
    assert counts["finance_nlp"] >= 6
    assert counts["sales_nlp"] + counts["support_nlp"] + counts["account_management_nlp"] >= 10
    assert counts["emotion_detection"] >= 8
    assert counts["embedding"] >= 8
    assert counts["reranker"] >= 4
    assert counts["long_context"] >= 4
    assert all(row["validated_now"] is False for row in rows)


def test_missing_required_tool_field_fails(tmp_path: Path) -> None:
    payload = {"tools": [{"tool_name": "Broken"}]}
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "missing required field tool_id" in result.stdout


def test_duplicate_tool_id_fails(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "data/nlp_tools_registry.example.json").read_text(encoding="utf-8"))
    payload["tools"][1]["tool_id"] = payload["tools"][0]["tool_id"]
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "duplicate tool_id" in result.stdout


def test_validated_now_fails_until_real_benchmark_exists(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "data/nlp_tools_registry.example.json").read_text(encoding="utf-8"))
    payload["tools"][0]["validated_now"] = True
    path = tmp_path / "validated.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "validated_now must remain false" in result.stdout
