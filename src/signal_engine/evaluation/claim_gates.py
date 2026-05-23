from __future__ import annotations

FORBIDDEN_CLAIM_ERRORS = {
    "alpha": "NO_TRADING_CLAIM",
    "buy": "NO_TRADING_CLAIM",
    "sell": "NO_TRADING_CLAIM",
    "trading": "NO_TRADING_CLAIM",
    "statistical significance": "NO_SIGNIFICANCE_CLAIM",
    "statistically significant": "NO_SIGNIFICANCE_CLAIM",
    "causal": "NO_CAUSAL_CLAIM",
    "causes": "NO_CAUSAL_CLAIM",
}

MANDATORY_EVALUATION_DISCLAIMERS = [
    "NOT_ENOUGH_DATA",
    "EXPLORATORY_ONLY",
    "NO_SIGNIFICANCE_CLAIM",
    "NO_CAUSAL_CLAIM",
    "NO_TRADING_CLAIM",
]


def validate_claim_language(text: str) -> list[str]:
    lowered = text.lower()
    for disclaimer in MANDATORY_EVALUATION_DISCLAIMERS:
        lowered = lowered.replace(disclaimer.lower(), "")
    errors = sorted({error for marker, error in FORBIDDEN_CLAIM_ERRORS.items() if marker in lowered})
    return errors


def claim_disclaimers() -> list[str]:
    return list(MANDATORY_EVALUATION_DISCLAIMERS)
