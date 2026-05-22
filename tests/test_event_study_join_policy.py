from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _validate_payload(payload):
    path = Path(__file__).resolve().parents[1] / "scripts" / "validate_event_study_join_policy.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("validate_event_study_join_policy", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_payload(payload)


def test_event_study_join_policy_requires_controls_and_blocks_significance() -> None:
    payload = {
        "join_key": ["ticker", "fiscal_period"],
        "required_controls": {"market_proxy": "required"},
        "gates": {"min_events": 0, "min_gold_labels": 0, "significance_claim_allowed": True},
        "cases": [
            {
                "ticker": "MNL",
                "fiscal_period": "FY2024_Q2",
                "call_datetime": "2024-08-07T20:30:00Z",
                "market_session": "after_close",
                "earnings_surprise_status": "missing",
                "market_proxy": "SPY",
                "sector_proxy": "XLI",
                "confounder_notes": "synthetic",
                "gold_signal_join_status": "not_ready",
                "significance_claim_allowed": True,
            }
        ],
    }
    errors = _validate_payload(payload)
    assert "missing join key call_datetime" in errors
    assert "missing required control earnings_surprise_status" in errors
    assert "significance_claim_allowed must be false by default" in errors
    assert "case 1: significance_claim_allowed must be false" in errors
