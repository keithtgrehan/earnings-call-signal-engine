from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _validate_payload(payload):
    path = Path(__file__).resolve().parents[1] / "scripts" / "validate_experiment_design.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("validate_experiment_design", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_payload(payload)


def test_experiment_design_rejects_trading_metrics_and_significance() -> None:
    payload = {
        "variants": [{"variant_id": "deterministic_only", "deterministic_output_override_allowed": False}],
        "metrics": ["trading_performance"],
        "sample_gate": {"power_check_required_before_significance_language": False},
        "significance_claim_allowed": True,
        "multivariate": {},
    }
    errors = _validate_payload(payload)
    assert "forbidden primary metric 'trading_performance'" in errors
    assert "significance_claim_allowed must be false" in errors
    assert "sample gate must require power check before significance language" in errors
