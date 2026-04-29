from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import text_features as base_text_features
from .lexicons import load_loughran_mcdonald_lexicon, match_loughran_mcdonald_terms
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
    SALES_BUYER_INTENT_TERMS,
    SALES_COMPETITOR_TERMS,
    SALES_NEXT_STEP_TERMS,
    SALES_OBJECTION_TERMS,
    SALES_PRICING_TERMS,
    SUPPORT_DEFLECTION_TERMS,
    SUPPORT_ESCALATION_TERMS,
    SUPPORT_FRUSTRATION_TERMS,
    SUPPORT_RESOLUTION_TERMS,
)


SIGNAL_FAMILY_LABELS: tuple[str, ...] = (
    "risk_friction",
    "opportunity_commitment",
    "uncertainty_hedging",
    "neutral",
)
HUMAN_REVIEWED_LABELS_RELATIVE_PATH = "data/nlp_research/human_reviewed_signal_labels.jsonl"
DEFAULT_RANDOM_SEED = 42
DEFAULT_TEST_SIZE = 0.33
MIN_CLASS_SUPPORT = 2
MIN_TOTAL_EXAMPLES = 12

RISK_FRICTION_TERMS: tuple[str, ...] = tuple(
    dict.fromkeys(
        [
            *SUPPORT_FRUSTRATION_TERMS,
            *SUPPORT_DEFLECTION_TERMS,
            *SUPPORT_ESCALATION_TERMS,
            *SALES_OBJECTION_TERMS,
            *SALES_PRICING_TERMS,
            *SALES_COMPETITOR_TERMS,
            *ACCOUNT_CHURN_RISK_TERMS,
            *ACCOUNT_RENEWAL_RISK_TERMS,
            *ACCOUNT_UNRESOLVED_TERMS,
            *EARNINGS_ANALYST_PRESSURE_TERMS,
        ]
    )
)
OPPORTUNITY_COMMITMENT_TERMS: tuple[str, ...] = tuple(
    dict.fromkeys(
        [
            *SUPPORT_RESOLUTION_TERMS,
            *SALES_BUYER_INTENT_TERMS,
            *SALES_NEXT_STEP_TERMS,
            *ACCOUNT_EXPANSION_TERMS,
            *ACCOUNT_COMMITMENT_TERMS,
            *EARNINGS_CONFIDENCE_TERMS,
            *EARNINGS_FOLLOW_UP_TERMS,
        ]
    )
)
UNCERTAINTY_HEDGING_TERMS: tuple[str, ...] = tuple(
    dict.fromkeys(
        [
            *HEDGING_TERMS,
            *EARNINGS_GUIDANCE_CAUTION_TERMS,
            "not sure",
            "unclear",
            "visibility",
            "for now",
            "probably",
            "it depends",
            "may",
            "might",
        ]
    )
)

FIXTURE_SPECS: tuple[tuple[str, str], ...] = (
    ("data/signal_engine_2_0/sample_support.json", "support"),
    ("data/signal_engine_2_0/sample_sales.json", "sales"),
    ("data/signal_engine_2_0/sample_account_management.json", "account_management"),
    ("data/signal_engine_2_0/fixtures/support_tickets_realistic.jsonl", "support"),
    ("data/signal_engine_2_0/fixtures/sales_calls_realistic.jsonl", "sales"),
    ("data/signal_engine_2_0/fixtures/account_management_realistic.jsonl", "account_management"),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def fixture_paths(root: Path | None = None) -> list[tuple[Path, str]]:
    repo_root = root or _repo_root()
    return [(repo_root / relative_path, domain) for relative_path, domain in FIXTURE_SPECS]


def _load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
        return records
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    raise ValueError(f"Unsupported fixture payload at {path}")


def collect_local_signal_examples(root: Path | None = None) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for path, domain in fixture_paths(root=root):
        for record in _load_records(path):
            conversation_id = str(record.get("conversation_id") or record.get("call_id") or path.stem)
            transcript_segments = record.get("transcript_segments") or record.get("messages") or []
            if not isinstance(transcript_segments, list):
                continue
            for index, segment in enumerate(transcript_segments):
                if not isinstance(segment, dict):
                    continue
                text = str(segment.get("text") or segment.get("message") or segment.get("content") or "").strip()
                if not text:
                    continue
                examples.append(
                    {
                        "conversation_id": conversation_id,
                        "domain": domain,
                        "message_index": int(segment.get("message_index", index)),
                        "role": str(segment.get("role") or segment.get("speaker_role") or "").strip().lower(),
                        "text": text,
                        "source_path": str(path.relative_to(root or _repo_root())),
                    }
                )
    return examples


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    matches = [term for term in terms if base_text_features.term_found(text, term)]
    return matches[:8]


def _loughran_mcdonald_scores(text: str) -> dict[str, Any]:
    lexicon = load_loughran_mcdonald_lexicon()
    matches = match_loughran_mcdonald_terms(text, lexicon=lexicon)
    negative_terms = list(dict.fromkeys([*matches["negative"], *matches["litigious"], *matches["constraining"]]))
    positive_terms = list(dict.fromkeys(matches["positive"]))
    uncertainty_terms = list(dict.fromkeys([*matches["uncertainty"], *matches["modal"]]))
    return {
        "matches": matches,
        "risk_friction_terms": negative_terms[:8],
        "opportunity_commitment_terms": positive_terms[:8],
        "uncertainty_hedging_terms": uncertainty_terms[:8],
        "available": any(bool(lexicon.get(category)) for category in lexicon),
    }


def weak_label_signal_family(
    text: str,
    *,
    domain: str | None = None,
) -> dict[str, Any]:
    risk_matches = _matched_terms(text, RISK_FRICTION_TERMS)
    opportunity_matches = _matched_terms(text, OPPORTUNITY_COMMITMENT_TERMS)
    uncertainty_matches = _matched_terms(text, UNCERTAINTY_HEDGING_TERMS)
    lm_support = _loughran_mcdonald_scores(text)
    lm_risk_matches = lm_support["risk_friction_terms"]
    lm_opportunity_matches = lm_support["opportunity_commitment_terms"]
    lm_uncertainty_matches = lm_support["uncertainty_hedging_terms"]

    scores = {
        "risk_friction": (len(risk_matches) * 2) + len(lm_risk_matches),
        "opportunity_commitment": (len(opportunity_matches) * 2) + len(lm_opportunity_matches),
        "uncertainty_hedging": (len(uncertainty_matches) * 2) + len(lm_uncertainty_matches),
        "neutral": 0,
    }

    label = "neutral"
    evidence_terms: list[str] = []
    if scores["risk_friction"] > 0 or scores["opportunity_commitment"] > 0 or scores["uncertainty_hedging"] > 0:
        ordered = sorted(
            (
                ("risk_friction", list(dict.fromkeys([*risk_matches, *lm_risk_matches]))),
                ("opportunity_commitment", list(dict.fromkeys([*opportunity_matches, *lm_opportunity_matches]))),
                ("uncertainty_hedging", list(dict.fromkeys([*uncertainty_matches, *lm_uncertainty_matches]))),
            ),
            key=lambda item: (len(item[1]), item[0] == "risk_friction", item[0] == "uncertainty_hedging"),
            reverse=True,
        )
        label, evidence_terms = ordered[0]

    reason = {
        "risk_friction": "Matched deterministic friction, pricing, escalation, or unresolved-issue terms.",
        "opportunity_commitment": "Matched deterministic commitment, resolution, next-step, or expansion terms.",
        "uncertainty_hedging": "Matched deterministic hedging or visibility-caution terms.",
        "neutral": "No deterministic weak-label terms were matched.",
    }[label]
    return {
        "label": label,
        "evidence_terms": evidence_terms,
        "reason": reason,
        "domain": domain,
        "loughran_mcdonald_available": lm_support["available"],
        "loughran_mcdonald_matches": lm_support["matches"],
    }


def build_weak_labeled_examples(root: Path | None = None) -> list[dict[str, Any]]:
    labeled_examples: list[dict[str, Any]] = []
    for example in collect_local_signal_examples(root=root):
        weak_label = weak_label_signal_family(example["text"], domain=example["domain"])
        labeled_examples.append({**example, "signal_family": weak_label["label"], "evidence_terms": weak_label["evidence_terms"], "label_reason": weak_label["reason"]})
    return labeled_examples


def predict_deterministic_signal_family(
    text: str,
    *,
    domain: str | None = None,
) -> dict[str, Any]:
    return weak_label_signal_family(text, domain=domain)


def label_support_counts(examples: list[dict[str, Any]]) -> dict[str, int]:
    counts = {label: 0 for label in SIGNAL_FAMILY_LABELS}
    for example in examples:
        label = str(example.get("signal_family") or example.get("label") or "")
        if label in counts:
            counts[label] += 1
    return counts


def training_readiness(examples: list[dict[str, Any]]) -> dict[str, Any]:
    counts = label_support_counts(examples)
    insufficient_labels = [label for label, count in counts.items() if count < MIN_CLASS_SUPPORT]
    ready = len(examples) >= MIN_TOTAL_EXAMPLES and not insufficient_labels
    return {
        "ready": ready,
        "total_examples": len(examples),
        "label_support": counts,
        "minimum_examples_per_class": MIN_CLASS_SUPPORT,
        "minimum_total_examples": MIN_TOTAL_EXAMPLES,
        "insufficient_labels": insufficient_labels,
        "reason": (
            "weak-label corpus is ready for a bounded train/test split"
            if ready
            else "local weak-label corpus is too small or imbalanced for an honest 4-class benchmark split"
        ),
    }


def load_supervised_examples(path: Path) -> list[dict[str, Any]]:
    examples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"Expected JSON object rows in {path}")
        text = str(row.get("text", "")).strip()
        label = str(row.get("signal_family") or row.get("label") or "").strip()
        if not text or label not in SIGNAL_FAMILY_LABELS:
            raise ValueError(f"Invalid labeled example in {path}: {row}")
        examples.append(
            {
                "id": str(row.get("id") or f"{path.stem}:{len(examples)}"),
                "text": text,
                "signal_family": label,
                "source_path": str(row.get("source_path") or path.name),
                "source_file": str(row.get("source_file") or row.get("source_path") or path.name),
                "conversation_id": str(row.get("conversation_id") or row.get("source_path") or path.stem),
                "message_index": int(row.get("message_index", 0)),
                "domain": str(row.get("domain") or "unknown"),
                "evidence_terms": list(row.get("evidence_terms") or []),
                "label_source": str(row.get("label_source") or "unknown"),
                "rationale": str(row.get("rationale") or ""),
                "pii_redacted": bool(row.get("pii_redacted", False)),
                "notes": str(row.get("notes") or ""),
            }
        )
    return examples


def render_support_markdown_table(label_support: dict[str, int]) -> str:
    lines = ["| label | support |", "| --- | --- |"]
    for label in SIGNAL_FAMILY_LABELS:
        lines.append(f"| {label} | {label_support.get(label, 0)} |")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_RANDOM_SEED",
    "DEFAULT_TEST_SIZE",
    "HUMAN_REVIEWED_LABELS_RELATIVE_PATH",
    "SIGNAL_FAMILY_LABELS",
    "build_weak_labeled_examples",
    "collect_local_signal_examples",
    "fixture_paths",
    "label_support_counts",
    "load_supervised_examples",
    "predict_deterministic_signal_family",
    "render_support_markdown_table",
    "training_readiness",
    "weak_label_signal_family",
]
