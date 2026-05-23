from __future__ import annotations

import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _status(ok: bool, detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": "ok" if ok else "warning", "detail": detail, **extra}


def run_doctor() -> dict[str, Any]:
    reports_dir = ROOT / "reports"
    checks: dict[str, dict[str, Any]] = {}
    checks["python_version"] = _status(sys.version_info >= (3, 11), platform.python_version(), required=">=3.11")
    checks["package_import"] = _status(importlib.util.find_spec("signal_engine") is not None, "signal_engine importable")
    checks["repo_root"] = _status((ROOT / "pyproject.toml").exists() and (ROOT / "AGENTS.md").exists(), str(ROOT))
    checks["reports_writable"] = _check_reports_writable(reports_dir)
    checks["required_configs"] = _check_required_paths(
        [
            ROOT / "configs" / "training_plan.example.yml",
            ROOT / "configs" / "claims_matrix.example.yml",
            ROOT / "configs" / "resource_registry.example.yml",
            ROOT / "configs" / "nyse_30_pilot_targets.yml",
        ]
    )
    checks["gold_label_file"] = _check_gold_file(ROOT / "data" / "gold" / "gold_labels.jsonl")
    checks["optional_deps"] = _check_optional_deps(["yaml", "pandas", "rich", "pytest", "ruff"])
    checks["core_proof_commands"] = _check_required_paths(
        [
            ROOT / "scripts" / "audit_gold_labels.py",
            ROOT / "scripts" / "report_first_100_review_metrics.py",
            ROOT / "scripts" / "run_training_readiness.py",
            ROOT / "scripts" / "report_agent5_acquisition_status.py",
            ROOT / "scripts" / "agent1_error_analysis.py",
        ]
    )
    checks["provider_credentials"] = _status(True, "core path does not require provider credentials")
    status = "ok" if all(check["status"] == "ok" for check in checks.values() if check) else "warning"
    return {
        "status": status,
        "repo_root": str(ROOT),
        "provider_credentials_required": False,
        "checks": checks,
    }


def _check_reports_writable(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".doctor_write_check"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
        return _status(True, str(path))
    except OSError as exc:
        return _status(False, str(exc))


def _check_required_paths(paths: list[Path]) -> dict[str, Any]:
    missing = [str(path) for path in paths if not path.exists()]
    return _status(not missing, "all required paths present" if not missing else "missing required paths", missing=missing)


def _check_gold_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _status(False, "canonical gold file missing", path=str(path))
    return _status(True, "canonical gold file present", path=str(path), size_bytes=path.stat().st_size)


def _check_optional_deps(module_names: list[str]) -> dict[str, Any]:
    present = []
    missing = []
    for name in module_names:
        if shutil.which(name) or importlib.util.find_spec(name) is not None:
            present.append(name)
        else:
            missing.append(name)
    return _status(True, "optional dependency probe complete", present=present, missing=missing)


def doctor_text(payload: dict[str, Any]) -> str:
    lines = ["Signal Engine doctor", f"status: {payload['status']}", f"repo_root: {payload['repo_root']}"]
    for name, check in payload["checks"].items():
        lines.append(f"- {name}: {check['status']} ({check['detail']})")
    return "\n".join(lines) + "\n"


def doctor_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
