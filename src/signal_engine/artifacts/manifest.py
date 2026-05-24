from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

ARTIFACT_MANIFEST_SCHEMA_VERSION = "1.0.0"

REQUIRED_MANIFEST_FIELDS = {
    "run_id",
    "git_sha",
    "command",
    "timestamp",
    "config_hash",
    "input_hashes",
    "output_hashes",
    "schema_versions",
    "environment_summary",
    "generated_by",
    "deterministic_core_version",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _hash_paths(paths: Iterable[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        resolved = Path(path)
        hashes[str(resolved)] = sha256_file(resolved) if resolved.exists() and resolved.is_file() else "missing"
    return hashes


def _git_sha() -> str:
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    except OSError:
        return "unknown"
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else "unknown"


def environment_summary() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
    }


def build_artifact_manifest(
    *,
    run_id: str,
    command: str,
    inputs: Iterable[Path] = (),
    outputs: Iterable[Path] = (),
    config_paths: Iterable[Path] = (),
    schema_versions: dict[str, str] | None = None,
    generated_by: str,
    deterministic_core_version: str,
) -> dict[str, Any]:
    config_hashes = _hash_paths(config_paths)
    return {
        "run_id": run_id,
        "git_sha": _git_sha(),
        "command": command,
        "timestamp": datetime.now(UTC).isoformat(),
        "config_hash": sha256_json(config_hashes),
        "input_hashes": _hash_paths(inputs),
        "output_hashes": _hash_paths(outputs),
        "schema_versions": {"artifact_manifest": ARTIFACT_MANIFEST_SCHEMA_VERSION, **(schema_versions or {})},
        "environment_summary": environment_summary(),
        "generated_by": generated_by,
        "deterministic_core_version": deterministic_core_version,
    }


def validate_artifact_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(REQUIRED_MANIFEST_FIELDS - set(manifest)):
        errors.append(f"missing required field {field}")
    for mapping_name in ("input_hashes", "output_hashes", "schema_versions", "environment_summary"):
        if mapping_name in manifest and not isinstance(manifest[mapping_name], dict):
            errors.append(f"{mapping_name} must be an object")
    for field in ("run_id", "git_sha", "command", "timestamp", "config_hash", "generated_by", "deterministic_core_version"):
        if field in manifest and not str(manifest.get(field, "")).strip():
            errors.append(f"{field} must be non-empty")
    if "config_hash" in manifest and not str(manifest.get("config_hash", "")).startswith("sha256:"):
        errors.append("config_hash must be sha256-prefixed")
    for mapping_name in ("input_hashes", "output_hashes"):
        for key, value in (manifest.get(mapping_name) or {}).items():
            if not str(key).strip():
                errors.append(f"{mapping_name} contains an empty path")
            if value != "missing" and not str(value).startswith("sha256:"):
                errors.append(f"{mapping_name}.{key} must be sha256-prefixed or missing")
    return errors


def write_artifact_manifest(path: Path, manifest: dict[str, Any]) -> None:
    errors = validate_artifact_manifest(manifest)
    if errors:
        raise ValueError("; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
