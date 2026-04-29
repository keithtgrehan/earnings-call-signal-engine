from __future__ import annotations

import json
from pathlib import Path

from signal_engine.pipeline import analyze_conversation_record, analyze_path
from signal_engine.schemas import SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "signal_engine_2_0"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_output_schema_shape_and_version() -> None:
    support_sample = _load_json(DATA_DIR / "sample_support.json")
    result = analyze_conversation_record(support_sample, domain="support")
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["domain"] == "support"
    assert result["conversation_id"] == support_sample["conversation_id"]
    assert set(result) == {
        "schema_version",
        "domain",
        "conversation_id",
        "scores",
        "risk_flags",
        "opportunity_flags",
        "evidence",
        "metadata",
    }
    assert result["metadata"]["deterministic"] is True
    assert result["metadata"]["external_api_required"] is False
    assert result["metadata"]["llm_required_for_canonical_scoring"] is False


def test_signal_engine_is_deterministic() -> None:
    sales_sample = _load_json(DATA_DIR / "sample_sales.json")
    first = analyze_conversation_record(sales_sample, domain="sales")
    second = analyze_conversation_record(sales_sample, domain="sales")
    assert first == second


def test_support_sample_triggers_support_risk_flag_with_evidence() -> None:
    result = analyze_path(DATA_DIR / "sample_support.json", domain="support")[0]
    assert any(flag.startswith("support_") for flag in result["risk_flags"])
    assert result["evidence"]
    assert all(set(item) == {"signal_name", "message_index", "matched_text", "reason"} for item in result["evidence"])


def test_sales_sample_triggers_sales_signal() -> None:
    result = analyze_path(DATA_DIR / "sample_sales.json", domain="sales")[0]
    assert any(flag.startswith("sales_") for flag in result["risk_flags"] + result["opportunity_flags"])
    assert result["scores"]["buyer_intent_score"] > 0
    assert result["scores"]["pricing_concern_mentions"] >= 1


def test_account_management_sample_triggers_renewal_churn_or_expansion_signal() -> None:
    result = analyze_path(DATA_DIR / "sample_account_management.json", domain="account_management")[0]
    joined_flags = result["risk_flags"] + result["opportunity_flags"]
    assert any(
        flag in {
            "account_churn_risk",
            "account_renewal_risk",
            "account_expansion_opportunity",
        }
        for flag in joined_flags
    )
    assert result["scores"]["unresolved_issue_count"] >= 1


def test_triggered_flags_have_supporting_evidence() -> None:
    result = analyze_path(DATA_DIR / "sample_account_management.json", domain="account_management")[0]
    assert result["risk_flags"] or result["opportunity_flags"]
    assert len(result["evidence"]) >= 2
    assert any(item["message_index"] is not None for item in result["evidence"])
