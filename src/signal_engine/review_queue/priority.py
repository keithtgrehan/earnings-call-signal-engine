from __future__ import annotations

import re
from typing import Any

from .schema import normalize_label

FINANCIAL_RE = re.compile(
    r"\b(guidance|outlook|expect|expected|expects|revenue|eps|margin|free cash flow|cash flow|capex|tariff|headwind|decline|range)\b",
    re.I,
)
QUANT_RE = re.compile(
    r"(\$[\d,.]+|\b\d+(?:\.\d+)?\s?%|\b\d+\s?(?:basis points|bps)\b|\b(?:fiscal|fy|calendar)\s?\d{2,4}\b|\bq[1-4]\b|\b\d{4}\b|\b\d+(?:\.\d+)?\s?(?:million|billion)\b)",
    re.I,
)
SUBSTANTIVE_RE = re.compile(
    r"\b(demand|supply|pricing|investment|competition|competitive|macro|uncertainty|pressure|strong demand|weakness|constraints?|customer behavior|customers?)\b",
    re.I,
)
BOILERPLATE_RE = re.compile(
    r"\b(gaap|non-gaap|sec filings?|factset|lseg|may now disconnect|call is being recorded|conference is being recorded|subject to risks and uncertainties|forward-looking statements?|actual results may differ|operator instructions|question-and-answer session|press star|risk factors|form 10-k|form 10q|form 8-k)\b",
    re.I,
)
BUSINESS_SPECIFIC_RE = re.compile(
    r"\b(demand|supply|pricing|investment|competition|macro|customer|headwind|decline|tariff|margin pressure|free cash flow|capex)\b",
    re.I,
)


def is_likely_boilerplate(text: str) -> bool:
    lowered = " ".join(str(text or "").lower().split())
    if not lowered:
        return False
    if BOILERPLATE_RE.search(lowered) and not BUSINESS_SPECIFIC_RE.search(lowered):
        return True
    pure_noise = len(lowered.split()) < 7 and bool(re.search(r"\b(thank you|operator|good morning|good afternoon)\b", lowered))
    return pure_noise


def rule_family(reason: str, source_type: str) -> str:
    lowered = str(reason or "").lower()
    if "analyst_pressure" in lowered:
        return "analyst_pressure"
    if "guidance_revision" in lowered or "guidance" in lowered:
        return "guidance_revision"
    if "weak" in source_type:
        return "weak_label"
    if "keyword" in lowered:
        return "keyword"
    return "packet_candidate"


def priority_for(row: dict[str, Any]) -> tuple[str, str, bool]:
    evidence = str(row.get("evidence_span") or "")
    reason = str(row.get("reason") or "")
    label = normalize_label(row.get("suggested_label"))
    combined = f"{reason}\n{evidence}"
    boilerplate = is_likely_boilerplate(evidence)

    if boilerplate:
        return "LOW", "low_boilerplate_or_disclaimer_text", True
    if label == "risk_friction":
        return "HIGH", "high_label_risk_friction", False
    if "analyst_pressure" in reason.lower():
        return "HIGH", "high_reason_analyst_pressure", False
    if "guidance_revision" in reason.lower():
        return "HIGH", "high_reason_guidance_revision", False
    if FINANCIAL_RE.search(combined):
        return "HIGH", "high_financial_guidance_or_outlook_term", False
    if QUANT_RE.search(combined):
        return "HIGH", "high_quantitative_or_future_period_term", False
    if label in {"opportunity_commitment", "uncertainty_hedging"} and SUBSTANTIVE_RE.search(combined):
        return "MEDIUM", "medium_substantive_business_context", False
    if SUBSTANTIVE_RE.search(combined):
        return "MEDIUM", "medium_business_context_keyword", False
    return "LOW", "low_keyword_noise_or_context_needed", False
