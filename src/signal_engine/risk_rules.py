from __future__ import annotations

from collections import defaultdict

from .domains import (
    ACCOUNT_CHURN_RISK_TERMS,
    ACCOUNT_COMMITMENT_TERMS,
    ACCOUNT_EXPANSION_TERMS,
    ACCOUNT_RENEWAL_RISK_TERMS,
    ACCOUNT_UNRESOLVED_TERMS,
    EARNINGS_ANALYST_PRESSURE_TERMS,
    EARNINGS_CONFIDENCE_TERMS,
    EARNINGS_FOLLOW_UP_TERMS,
    EARNINGS_GUIDANCE_CAUTION_TERMS,
    HEDGING_TERMS,
    NEGATIVE_TERMS,
    POSITIVE_TERMS,
    SALES_BUYER_INTENT_TERMS,
    SALES_COMPETITOR_TERMS,
    SALES_NEXT_STEP_TERMS,
    SALES_OBJECTION_TERMS,
    SALES_PRICING_TERMS,
    SUPPORT_DEFLECTION_TERMS,
    SUPPORT_DIRECT_ANSWER_TERMS,
    SUPPORT_ESCALATION_TERMS,
    SUPPORT_FRUSTRATION_TERMS,
    SUPPORT_RESOLUTION_TERMS,
)
from .role_features import build_response_pairs, internal_token_share, segments_for_group, unanswered_prompt_count
from .schemas import ConversationRecord, Evidence, TranscriptSegment
from .text_features import (
    DATE_OR_DEADLINE_RE,
    OWNER_COMMITMENT_RE,
    bounded_score,
    clamp,
    evidence_for_pattern,
    evidence_for_terms,
    sentiment_proxy_score,
    token_overlap_ratio,
)


def _unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _dedupe_evidence(evidence: list[Evidence]) -> list[Evidence]:
    seen: set[tuple[str, int | None, str, str]] = set()
    deduped: list[Evidence] = []
    for item in evidence:
        key = (item.signal_name, item.message_index, item.matched_text, item.reason)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _date_or_owner_evidence(
    segments: list[TranscriptSegment],
    *,
    signal_name: str,
    reason: str,
    roles: set[str] | None = None,
) -> list[Evidence]:
    evidence = evidence_for_pattern(
        segments,
        DATE_OR_DEADLINE_RE,
        signal_name=signal_name,
        reason=reason,
        roles=roles,
        limit=3,
    )
    evidence.extend(
        evidence_for_pattern(
            segments,
            OWNER_COMMITMENT_RE,
            signal_name=signal_name,
            reason=reason,
            roles=roles,
            limit=3,
        )
    )
    return _dedupe_evidence(evidence)


def _pair_directness(
    pairs,
    *,
    direct_terms: tuple[str, ...],
    deflection_terms: tuple[str, ...],
) -> tuple[float, list[Evidence], list[Evidence]]:
    pair_scores: list[float] = []
    low_directness_evidence: list[Evidence] = []
    deflection_evidence: list[Evidence] = []
    for pair in pairs:
        prompt = pair.prompt
        response = pair.response
        if response is None:
            pair_scores.append(0.0)
            deflection_evidence.append(
                Evidence(
                    signal_name="deflection",
                    message_index=prompt.message_index,
                    matched_text=prompt.text,
                    reason="Prompt did not receive a matching response turn.",
                )
            )
            continue

        overlap = token_overlap_ratio(prompt.text, response.text)
        direct_hit = any(term.lower() in response.text.lower() for term in direct_terms)
        hedge_hits = sum(1 for term in HEDGING_TERMS if term.lower() in response.text.lower())
        deflection_hit = any(term.lower() in response.text.lower() for term in deflection_terms)
        score = (0.65 * overlap) + (0.25 if direct_hit else 0.0) + (0.10 * max(0.0, 1 - (hedge_hits * 0.3)))
        if deflection_hit:
            score -= 0.35
            deflection_evidence.append(
                Evidence(
                    signal_name="deflection",
                    message_index=response.message_index,
                    matched_text=response.text,
                    reason="Response uses a deflection phrase instead of resolving the prompt.",
                )
            )
        score = round(clamp(score), 4)
        pair_scores.append(score)
        if score < 0.35:
            low_directness_evidence.append(
                Evidence(
                    signal_name="directness",
                    message_index=response.message_index,
                    matched_text=response.text,
                    reason="Low lexical overlap and few direct-answer cues in the response.",
                )
            )
    average_score = round(sum(pair_scores) / len(pair_scores), 4) if pair_scores else 0.0
    return average_score, _dedupe_evidence(low_directness_evidence), _dedupe_evidence(deflection_evidence)


def _build_result(
    scores: dict[str, float | int],
    risk_flags: list[str],
    opportunity_flags: list[str],
    evidence: list[Evidence],
) -> dict[str, object]:
    grouped: dict[str, list[Evidence]] = defaultdict(list)
    for item in _dedupe_evidence(evidence):
        grouped[item.signal_name].append(item)
    return {
        "scores": scores,
        "risk_flags": _unique_strings(risk_flags),
        "opportunity_flags": _unique_strings(opportunity_flags),
        "evidence": [item for items in grouped.values() for item in items],
    }


def analyze_support(record: ConversationRecord) -> dict[str, object]:
    pairs = build_response_pairs(record)
    profile_customer_roles = {"customer"}
    profile_internal_roles = {"agent"}

    directness_score, low_directness_evidence, structural_deflection_evidence = _pair_directness(
        pairs,
        direct_terms=SUPPORT_DIRECT_ANSWER_TERMS,
        deflection_terms=SUPPORT_DEFLECTION_TERMS,
    )
    deflection_evidence = evidence_for_terms(
        record.transcript_segments,
        SUPPORT_DEFLECTION_TERMS,
        signal_name="deflection",
        reason="Support deflection language detected.",
        roles=profile_internal_roles,
    )
    deflection_evidence.extend(structural_deflection_evidence)

    frustration_evidence = evidence_for_terms(
        record.transcript_segments,
        SUPPORT_FRUSTRATION_TERMS,
        signal_name="frustration",
        reason="Customer frustration language detected.",
        roles=profile_customer_roles,
    )
    escalation_evidence = evidence_for_terms(
        record.transcript_segments,
        SUPPORT_ESCALATION_TERMS,
        signal_name="escalation_risk",
        reason="Escalation language detected in the support exchange.",
    )
    resolution_evidence = evidence_for_terms(
        record.transcript_segments,
        SUPPORT_RESOLUTION_TERMS,
        signal_name="resolution_clarity",
        reason="Explicit resolution language detected.",
        roles=profile_internal_roles,
    )
    commitment_evidence = _date_or_owner_evidence(
        segments_for_group(record, "internal"),
        signal_name="resolution_clarity",
        reason="Support reply includes an owner or dated follow-up commitment.",
    )

    unanswered_count = unanswered_prompt_count(record)
    deflection_score = round(
        clamp((len(deflection_evidence) + unanswered_count) / max(1, len(pairs) + unanswered_count)),
        4,
    )
    frustration_score = bounded_score(len(frustration_evidence) + len(escalation_evidence), cap=4)
    resolution_clarity_score = round(
        clamp((0.55 * bounded_score(len(resolution_evidence), cap=2)) + (0.45 * bounded_score(len(commitment_evidence), cap=2))),
        4,
    )
    escalation_risk_score = round(
        clamp((0.45 * frustration_score) + (0.35 * deflection_score) + (0.20 * bounded_score(len(escalation_evidence), cap=2))),
        4,
    )

    scores = {
        "directness_score": directness_score,
        "deflection_score": deflection_score,
        "frustration_score": frustration_score,
        "resolution_clarity_score": resolution_clarity_score,
        "escalation_risk_score": escalation_risk_score,
    }
    risk_flags: list[str] = []
    opportunity_flags: list[str] = []
    evidence: list[Evidence] = []

    if directness_score < 0.35:
        risk_flags.append("support_low_directness")
        evidence.extend(low_directness_evidence[:2])
    if deflection_score >= 0.35:
        risk_flags.append("support_deflection")
        evidence.extend(deflection_evidence[:3])
    if frustration_score >= 0.3:
        risk_flags.append("support_frustration")
        evidence.extend(frustration_evidence[:2] or escalation_evidence[:1])
    if escalation_risk_score >= 0.45:
        risk_flags.append("support_escalation_risk")
        evidence.extend((escalation_evidence + frustration_evidence + deflection_evidence)[:3])
    if resolution_clarity_score >= 0.45:
        opportunity_flags.append("support_clear_resolution")
        evidence.extend((resolution_evidence + commitment_evidence)[:2])
    elif unanswered_count > 0:
        risk_flags.append("support_low_resolution_clarity")
        for pair in pairs:
            if pair.response is None:
                evidence.append(
                    Evidence(
                        signal_name="resolution_clarity",
                        message_index=pair.prompt.message_index,
                        matched_text=pair.prompt.text,
                        reason="Customer prompt is still open without a clear resolution turn.",
                    )
                )
                break

    return _build_result(scores, risk_flags, opportunity_flags, evidence)


def analyze_sales(record: ConversationRecord) -> dict[str, object]:
    buyer_segments = segments_for_group(record, "buyer")
    internal_segments = segments_for_group(record, "internal")

    buyer_intent_evidence = evidence_for_terms(
        buyer_segments,
        SALES_BUYER_INTENT_TERMS,
        signal_name="buyer_intent",
        reason="Buyer intent language detected.",
    )
    objection_evidence = evidence_for_terms(
        buyer_segments,
        SALES_OBJECTION_TERMS,
        signal_name="objection_count",
        reason="Buyer objection language detected.",
    )
    pricing_evidence = evidence_for_terms(
        buyer_segments,
        SALES_PRICING_TERMS,
        signal_name="pricing_concern",
        reason="Buyer raised pricing or budget concerns.",
    )
    competitor_evidence = evidence_for_terms(
        record.transcript_segments,
        SALES_COMPETITOR_TERMS,
        signal_name="competitor_mentions",
        reason="Competitor or alternative mention detected.",
    )
    next_step_evidence = evidence_for_terms(
        record.transcript_segments,
        SALES_NEXT_STEP_TERMS,
        signal_name="next_step_clarity",
        reason="Concrete next-step language detected.",
    )
    next_step_evidence.extend(
        _date_or_owner_evidence(
            internal_segments,
            signal_name="next_step_clarity",
            reason="Seller committed to a dated next step or owner.",
        )
    )

    buyer_intent_score = bounded_score(len(buyer_intent_evidence), cap=3)
    objection_count = len(objection_evidence)
    pricing_concern_count = len(pricing_evidence)
    next_step_clarity_score = round(
        clamp((0.6 * bounded_score(len(next_step_evidence), cap=3)) + (0.4 * min(1.0, buyer_intent_score + 0.1))),
        4,
    )
    competitor_mention_count = len(competitor_evidence)
    rep_overtalk_ratio = internal_token_share(record)

    scores = {
        "buyer_intent_score": buyer_intent_score,
        "objection_count": objection_count,
        "pricing_concern_mentions": pricing_concern_count,
        "next_step_clarity_score": next_step_clarity_score,
        "competitor_mentions": competitor_mention_count,
        "rep_overtalk_ratio": rep_overtalk_ratio,
    }
    risk_flags: list[str] = []
    opportunity_flags: list[str] = []
    evidence: list[Evidence] = []

    if pricing_concern_count > 0:
        risk_flags.append("sales_pricing_risk")
        evidence.extend(pricing_evidence[:2])
    if objection_count >= 1:
        risk_flags.append("sales_objection_pressure")
        evidence.extend(objection_evidence[:2])
    if competitor_mention_count > 0:
        risk_flags.append("sales_competitor_pressure")
        evidence.extend(competitor_evidence[:2])
    if rep_overtalk_ratio > 0.68:
        risk_flags.append("sales_rep_overtalk")
        for segment in internal_segments[:1]:
            evidence.append(
                Evidence(
                    signal_name="rep_overtalk_ratio",
                    message_index=segment.message_index,
                    matched_text=segment.text,
                    reason="Seller dominates the transcript token share.",
                )
            )
    if buyer_intent_score >= 0.35:
        opportunity_flags.append("sales_buyer_intent")
        evidence.extend(buyer_intent_evidence[:2])
    if next_step_clarity_score >= 0.4:
        opportunity_flags.append("sales_next_step_defined")
        evidence.extend(next_step_evidence[:2])
    elif buyer_intent_score >= 0.35:
        risk_flags.append("sales_next_step_gap")
        if buyer_segments:
            evidence.append(
                Evidence(
                    signal_name="next_step_clarity",
                    message_index=buyer_segments[-1].message_index,
                    matched_text=buyer_segments[-1].text,
                    reason="Buyer intent is present but the transcript lacks a clear seller-owned next step.",
                )
            )

    return _build_result(scores, risk_flags, opportunity_flags, evidence)


def analyze_account_management(record: ConversationRecord) -> dict[str, object]:
    customer_segments = segments_for_group(record, "customer")
    internal_segments = segments_for_group(record, "internal")

    churn_evidence = evidence_for_terms(
        customer_segments,
        ACCOUNT_CHURN_RISK_TERMS,
        signal_name="churn_risk",
        reason="Customer language indicates possible churn or seat reduction risk.",
    )
    renewal_evidence = evidence_for_terms(
        record.transcript_segments,
        ACCOUNT_RENEWAL_RISK_TERMS,
        signal_name="renewal_risk",
        reason="Renewal risk language detected.",
    )
    expansion_evidence = evidence_for_terms(
        record.transcript_segments,
        ACCOUNT_EXPANSION_TERMS,
        signal_name="expansion_opportunity",
        reason="Expansion or upgrade language detected.",
    )
    unresolved_evidence = evidence_for_terms(
        record.transcript_segments,
        ACCOUNT_UNRESOLVED_TERMS,
        signal_name="unresolved_issue_count",
        reason="Unresolved issue language detected.",
    )
    commitment_evidence = evidence_for_terms(
        internal_segments,
        ACCOUNT_COMMITMENT_TERMS,
        signal_name="commitment_clarity",
        reason="Account team commitment language detected.",
    )
    commitment_evidence.extend(
        _date_or_owner_evidence(
            internal_segments,
            signal_name="commitment_clarity",
            reason="Account team includes a date or owner for follow-up.",
        )
    )

    churn_risk_score = bounded_score(len(churn_evidence), cap=3)
    renewal_risk_score = bounded_score(len(renewal_evidence), cap=3)
    expansion_opportunity_score = bounded_score(len(expansion_evidence), cap=3)
    unresolved_issue_count = len(unresolved_evidence) + unanswered_prompt_count(record)
    customer_sentiment_score = sentiment_proxy_score(
        customer_segments,
        positive_terms=POSITIVE_TERMS,
        negative_terms=NEGATIVE_TERMS,
    )
    commitment_clarity_score = round(
        clamp((0.65 * bounded_score(len(commitment_evidence), cap=3)) + (0.35 * customer_sentiment_score)),
        4,
    )

    scores = {
        "churn_risk_score": churn_risk_score,
        "renewal_risk_score": renewal_risk_score,
        "expansion_opportunity_score": expansion_opportunity_score,
        "unresolved_issue_count": unresolved_issue_count,
        "customer_sentiment_score": customer_sentiment_score,
        "commitment_clarity_score": commitment_clarity_score,
    }
    risk_flags: list[str] = []
    opportunity_flags: list[str] = []
    evidence: list[Evidence] = []

    if churn_risk_score >= 0.35:
        risk_flags.append("account_churn_risk")
        evidence.extend(churn_evidence[:2])
    if renewal_risk_score >= 0.35:
        risk_flags.append("account_renewal_risk")
        evidence.extend(renewal_evidence[:2])
    if unresolved_issue_count > 0:
        risk_flags.append("account_unresolved_issues")
        evidence.extend(unresolved_evidence[:2])
    if customer_sentiment_score < 0.45 and (churn_risk_score > 0 or renewal_risk_score > 0):
        risk_flags.append("account_negative_sentiment")
        if customer_segments:
            evidence.append(
                Evidence(
                    signal_name="customer_sentiment_score",
                    message_index=customer_segments[0].message_index,
                    matched_text=customer_segments[0].text,
                    reason="Customer sentiment skews negative alongside churn or renewal risk cues.",
                )
            )
    if expansion_opportunity_score >= 0.35:
        opportunity_flags.append("account_expansion_opportunity")
        evidence.extend(expansion_evidence[:2])
    if commitment_clarity_score >= 0.45:
        opportunity_flags.append("account_commitment_defined")
        evidence.extend(commitment_evidence[:2])

    return _build_result(scores, risk_flags, opportunity_flags, evidence)


def analyze_earnings_call(record: ConversationRecord) -> dict[str, object]:
    analyst_segments = segments_for_group(record, "analyst")
    internal_segments = segments_for_group(record, "internal")

    analyst_pressure_evidence = evidence_for_terms(
        analyst_segments,
        EARNINGS_ANALYST_PRESSURE_TERMS,
        signal_name="analyst_pressure",
        reason="Analyst pressure or clarification language detected.",
    )
    guidance_caution_evidence = evidence_for_terms(
        record.transcript_segments,
        EARNINGS_GUIDANCE_CAUTION_TERMS,
        signal_name="guidance_caution",
        reason="Guidance caution language detected.",
    )
    confidence_evidence = evidence_for_terms(
        internal_segments,
        EARNINGS_CONFIDENCE_TERMS,
        signal_name="confidence_language",
        reason="Management confidence language detected.",
    )
    follow_up_evidence = evidence_for_terms(
        record.transcript_segments,
        EARNINGS_FOLLOW_UP_TERMS,
        signal_name="follow_up_commitment",
        reason="Follow-up commitment language detected.",
    )
    _, low_directness_evidence, deflection_evidence = _pair_directness(
        build_response_pairs(record),
        direct_terms=EARNINGS_CONFIDENCE_TERMS,
        deflection_terms=EARNINGS_FOLLOW_UP_TERMS,
    )

    scores = {
        "analyst_pressure_score": bounded_score(len(analyst_pressure_evidence), cap=3),
        "guidance_caution_score": bounded_score(len(guidance_caution_evidence), cap=3),
        "confidence_language_score": bounded_score(len(confidence_evidence), cap=3),
        "deflection_score": bounded_score(len(deflection_evidence), cap=3),
        "follow_up_commitment_score": bounded_score(len(follow_up_evidence), cap=3),
    }
    risk_flags: list[str] = []
    opportunity_flags: list[str] = []
    evidence: list[Evidence] = []

    if scores["analyst_pressure_score"] >= 0.35:
        risk_flags.append("earnings_analyst_pressure")
        evidence.extend(analyst_pressure_evidence[:2])
    if scores["guidance_caution_score"] >= 0.35:
        risk_flags.append("earnings_guidance_caution")
        evidence.extend(guidance_caution_evidence[:2])
    if scores["deflection_score"] >= 0.35:
        risk_flags.append("earnings_answer_deflection")
        evidence.extend((deflection_evidence + low_directness_evidence)[:2])
    if scores["confidence_language_score"] >= 0.35:
        opportunity_flags.append("earnings_management_confidence")
        evidence.extend(confidence_evidence[:2])
    if scores["follow_up_commitment_score"] >= 0.35:
        opportunity_flags.append("earnings_follow_up_commitment")
        evidence.extend(follow_up_evidence[:2])

    return _build_result(scores, risk_flags, opportunity_flags, evidence)


DOMAIN_ANALYZERS = {
    "support": analyze_support,
    "sales": analyze_sales,
    "account_management": analyze_account_management,
    "earnings_call": analyze_earnings_call,
}


def analyze_domain(record: ConversationRecord) -> dict[str, object]:
    return DOMAIN_ANALYZERS[record.domain](record)
