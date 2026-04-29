from __future__ import annotations

from typing import Iterable

from signal_engine.domains import (
    ACCOUNT_CHURN_RISK_TERMS,
    ACCOUNT_COMMITMENT_TERMS,
    ACCOUNT_RENEWAL_RISK_TERMS,
    EARNINGS_ANALYST_PRESSURE_TERMS,
    EARNINGS_CONFIDENCE_TERMS,
    EARNINGS_GUIDANCE_CAUTION_TERMS,
    HEDGING_TERMS,
    SALES_OBJECTION_TERMS,
    SALES_PRICING_TERMS,
    SUPPORT_ESCALATION_TERMS,
    SUPPORT_RESOLUTION_TERMS,
)
from signal_engine.text_features import lexical_density, term_found, tokenize

from .schemas import EvidenceSpan, ModalityFeatureSet, SignalFeature


TEXT_SIGNAL_MAP: dict[str, tuple[str, ...]] = {
    "uncertainty": tuple(
        dict.fromkeys(
            [
                *HEDGING_TERMS,
                *EARNINGS_GUIDANCE_CAUTION_TERMS,
                "not sure",
                "unclear",
                "visibility",
                "for now",
            ]
        )
    ),
    "hedging": tuple(dict.fromkeys([*HEDGING_TERMS, "may", "might", "could", "probably"])),
    "reassurance": tuple(
        dict.fromkeys(
            [
                *SUPPORT_RESOLUTION_TERMS,
                *ACCOUNT_COMMITMENT_TERMS,
                *EARNINGS_CONFIDENCE_TERMS,
                "i will",
                "we will",
                "send a plan",
            ]
        )
    ),
    "pressure": tuple(
        dict.fromkeys(
            [
                *SALES_OBJECTION_TERMS,
                *SALES_PRICING_TERMS,
                *EARNINGS_ANALYST_PRESSURE_TERMS,
                *SUPPORT_ESCALATION_TERMS,
            ]
        )
    ),
    "contradiction": (
        "however",
        "but",
        "still",
        "yet",
        "does not solve",
        "that feels vague",
        "another team",
    ),
    "escalation_risk": tuple(
        dict.fromkeys(
            [
                *SUPPORT_ESCALATION_TERMS,
                *ACCOUNT_CHURN_RISK_TERMS,
                *ACCOUNT_RENEWAL_RISK_TERMS,
                "dispute",
                "switch",
            ]
        )
    ),
}

RECOMMENDED_ACTIONS = {
    "uncertainty": "Review hedged language against concrete dates, owners, and commitments.",
    "hedging": "Check whether cautious language is acceptable or hides a missing commitment.",
    "reassurance": "Verify that reassurance is backed by a concrete plan rather than a generic promise.",
    "pressure": "Review the objection, pressure, or analyst challenge before deciding severity.",
    "contradiction": "Compare the surrounding turns to see whether the speaker is walking back a prior statement.",
    "escalation_risk": "Escalate for human review if unresolved operational risk keeps increasing.",
}


def _first_span(text: str, terms: Iterable[str]) -> EvidenceSpan | None:
    lowered = text.lower()
    for term in terms:
        index = lowered.find(term.lower())
        if index >= 0:
            return EvidenceSpan(text=text[index : index + len(term)], start_char=index, end_char=index + len(term))
    return None


def _matched_terms(text: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if term_found(text, term)]


def _strength_from_count(count: int) -> str:
    if count >= 3:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


def _confidence_from_count(count: int) -> float:
    return min(0.82, 0.34 + (0.12 * max(count, 1)))


def extract_text_feature_set(
    text: str,
    *,
    domain: str | None = None,
    source_path: str | None = None,
) -> ModalityFeatureSet:
    normalized_text = str(text or "").strip()
    if not normalized_text:
        return ModalityFeatureSet(
            modality="transcript",
            available=False,
            source_path=source_path,
            limitations=["No transcript text was provided."],
            adapter_used="deterministic_lexical_rules",
        )

    signals: list[SignalFeature] = []
    for signal_name, terms in TEXT_SIGNAL_MAP.items():
        matches = _matched_terms(normalized_text, terms)
        if not matches:
            continue
        signals.append(
            SignalFeature(
                signal_name=signal_name,
                modality="transcript",
                strength=_strength_from_count(len(matches)),
                confidence=_confidence_from_count(len(matches)),
                reason=f"Matched deterministic transcript cues: {', '.join(matches[:4])}.",
                recommended_review_action=RECOMMENDED_ACTIONS[signal_name],
                evidence_span=_first_span(normalized_text, matches),
                measurements={"match_count": len(matches), "matched_terms": matches[:8], "domain": domain},
            )
        )

    limitations = [
        "Signals are review cues, not claims about internal state.",
        "Transcript features remain canonical; audio and video are optional support only.",
    ]
    if domain == "earnings":
        limitations.append("Guidance and analyst-pressure cues still require human review in context.")

    return ModalityFeatureSet(
        modality="transcript",
        available=True,
        source_path=source_path,
        measurements={
            "character_count": len(normalized_text),
            "token_count": len(tokenize(normalized_text)),
            "lexical_density": lexical_density(normalized_text),
            "matched_signal_count": len(signals),
        },
        signals=signals,
        limitations=limitations,
        adapter_used="deterministic_lexical_rules",
    )


__all__ = ["extract_text_feature_set"]
