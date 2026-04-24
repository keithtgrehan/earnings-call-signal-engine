from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_DOMAINS = ("support", "sales", "account_management", "earnings_call")

ROLE_ALIASES = {
    "user": "customer",
    "end_user": "customer",
    "requester": "customer",
    "client": "customer",
    "prospect": "buyer",
    "champion": "buyer",
    "decision_maker": "buyer",
    "sales_rep": "rep",
    "seller": "rep",
    "account_executive": "rep",
    "ae": "rep",
    "customer_success_manager": "account_manager",
    "csm": "account_manager",
    "customer_success": "account_manager",
    "executive_sponsor": "account_manager",
    "management": "executive",
    "ceo": "executive",
    "cfo": "executive",
    "coo": "executive",
    "ir": "executive",
    "investor_relations": "executive",
}

POSITIVE_TERMS = (
    "clear",
    "confident",
    "fixed",
    "helpful",
    "improve",
    "improved",
    "on track",
    "resolved",
    "stable",
    "strong",
    "thank you",
    "working",
)

NEGATIVE_TERMS = (
    "angry",
    "blocked",
    "broken",
    "cancel",
    "complaint",
    "concern",
    "delay",
    "delayed",
    "error",
    "frustrated",
    "issue",
    "problem",
    "risk",
    "unacceptable",
    "unresolved",
    "upset",
)

HEDGING_TERMS = (
    "approximately",
    "assume",
    "believe",
    "could",
    "likely",
    "maybe",
    "might",
    "possibly",
    "probably",
    "roughly",
    "seems",
)

SUPPORT_DIRECT_ANSWER_TERMS = (
    "because",
    "here is what happened",
    "i can confirm",
    "i checked",
    "i fixed",
    "the fix is",
    "the reason is",
    "we resolved",
    "you can",
)

SUPPORT_DEFLECTION_TERMS = (
    "another team",
    "check the faq",
    "follow up later",
    "not in my queue",
    "please contact billing",
    "please refer to",
    "someone will reach out",
    "we are looking into it",
)

SUPPORT_FRUSTRATION_TERMS = (
    "again",
    "frustrated",
    "ridiculous",
    "still not working",
    "still waiting",
    "third time",
    "unacceptable",
    "upset",
)

SUPPORT_RESOLUTION_TERMS = (
    "case closed",
    "fixed",
    "issue is closed",
    "refund has been issued",
    "replacement sent",
    "resolved",
    "working now",
)

SUPPORT_ESCALATION_TERMS = (
    "chargeback",
    "complaint",
    "escalate",
    "legal",
    "manager",
    "supervisor",
)

SALES_BUYER_INTENT_TERMS = (
    "budget approved",
    "demo",
    "implementation",
    "legal review",
    "pilot",
    "poc",
    "procurement",
    "proposal",
    "rollout",
    "security review",
    "start next month",
    "trial",
)

SALES_OBJECTION_TERMS = (
    "concern",
    "expensive",
    "integration risk",
    "not convinced",
    "not ready",
    "security concern",
    "too complex",
    "too expensive",
    "worried",
)

SALES_PRICING_TERMS = (
    "budget",
    "cheaper",
    "cost",
    "discount",
    "expensive",
    "license fee",
    "price",
    "pricing",
    "roi",
    "seat cost",
)

SALES_NEXT_STEP_TERMS = (
    "book a demo",
    "follow up",
    "legal review",
    "next step",
    "pilot plan",
    "pricing options",
    "procurement",
    "proposal",
    "schedule",
    "send",
)

SALES_COMPETITOR_TERMS = (
    "alternative",
    "competitor",
    "freshdesk",
    "gainsight",
    "hubspot",
    "intercom",
    "salesforce",
    "zendesk",
)

ACCOUNT_CHURN_RISK_TERMS = (
    "cancel",
    "cut seats",
    "downgrade",
    "leave",
    "look at another vendor",
    "not renewing",
    "replace",
    "switch",
    "terminate",
)

ACCOUNT_RENEWAL_RISK_TERMS = (
    "budget freeze",
    "legal delay",
    "not sure we will renew",
    "procurement delay",
    "renewal",
    "reviewing vendors",
)

ACCOUNT_EXPANSION_TERMS = (
    "add seats",
    "additional team",
    "enterprise package",
    "expand",
    "expansion",
    "new business unit",
    "rollout",
    "upgrade",
)

ACCOUNT_UNRESOLVED_TERMS = (
    "outstanding issue",
    "pending fix",
    "still broken",
    "still dealing with",
    "still open",
    "unresolved",
    "waiting on",
)

ACCOUNT_COMMITMENT_TERMS = (
    "action items",
    "follow up",
    "i own",
    "owner",
    "recovery plan",
    "renewal review",
    "schedule",
    "send",
    "we will deliver",
)

EARNINGS_ANALYST_PRESSURE_TERMS = (
    "can you clarify",
    "follow up on",
    "help us understand",
    "what changed",
    "why should we believe",
)

EARNINGS_GUIDANCE_CAUTION_TERMS = (
    "cautious",
    "headwind",
    "macro",
    "not providing guidance",
    "uncertain",
    "variability",
)

EARNINGS_CONFIDENCE_TERMS = (
    "confident",
    "durable",
    "on track",
    "remain confident",
    "strong demand",
    "visibility",
)

EARNINGS_FOLLOW_UP_TERMS = (
    "after the call",
    "investor relations",
    "offline",
    "we will follow up",
)


@dataclass(frozen=True)
class DomainProfile:
    name: str
    prompt_group: str
    response_group: str
    role_groups: dict[str, frozenset[str]]


DOMAIN_PROFILES = {
    "support": DomainProfile(
        name="support",
        prompt_group="external",
        response_group="internal",
        role_groups={
            "external": frozenset({"customer"}),
            "internal": frozenset({"agent"}),
        },
    ),
    "sales": DomainProfile(
        name="sales",
        prompt_group="buyer",
        response_group="internal",
        role_groups={
            "buyer": frozenset({"buyer", "customer"}),
            "internal": frozenset({"rep"}),
        },
    ),
    "account_management": DomainProfile(
        name="account_management",
        prompt_group="customer",
        response_group="internal",
        role_groups={
            "customer": frozenset({"customer"}),
            "internal": frozenset({"account_manager"}),
        },
    ),
    "earnings_call": DomainProfile(
        name="earnings_call",
        prompt_group="analyst",
        response_group="internal",
        role_groups={
            "analyst": frozenset({"analyst"}),
            "internal": frozenset({"executive"}),
            "neutral": frozenset({"operator"}),
        },
    ),
}


def get_domain_profile(domain: str) -> DomainProfile:
    if domain not in DOMAIN_PROFILES:
        raise ValueError(f"Unsupported domain: {domain!r}. Expected one of {SUPPORTED_DOMAINS}.")
    return DOMAIN_PROFILES[domain]
