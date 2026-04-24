from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

TOKEN_RE = re.compile(r"[a-zA-Z']+")

# Compact in-repo subsets from Loughran-McDonald positive/negative/uncertainty style categories,
# with a few support-domain operational variants so the deterministic QA path stays useful.
LOUGHRAN_MCDONALD_POSITIVE = {
    "able",
    "benefit",
    "beneficial",
    "confident",
    "constructive",
    "effective",
    "efficient",
    "excellent",
    "improve",
    "improved",
    "improvement",
    "positive",
    "progress",
    "resolve",
    "resolved",
    "responsive",
    "satisfied",
    "smooth",
    "stable",
    "strength",
    "strong",
    "success",
    "successful",
    "supportive",
    "timely",
    "trust",
}

LOUGHRAN_MCDONALD_NEGATIVE = {
    "adverse",
    "angry",
    "complaint",
    "concern",
    "concerns",
    "delay",
    "delayed",
    "error",
    "escalation",
    "failure",
    "failed",
    "frustrated",
    "frustrating",
    "incorrect",
    "issue",
    "issues",
    "loss",
    "negative",
    "problem",
    "problems",
    "refund",
    "risk",
    "risky",
    "sorry",
    "unacceptable",
    "unclear",
    "unresolved",
    "upset",
    "weak",
    "wrong",
}

HEDGING_TERMS = {
    "approximately",
    "assume",
    "assuming",
    "believe",
    "could",
    "generally",
    "likely",
    "maybe",
    "might",
    "perhaps",
    "possibly",
    "probably",
    "roughly",
    "seems",
    "suggest",
    "typically",
    "usually",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "this",
    "to",
    "us",
    "we",
    "what",
    "when",
    "why",
    "will",
    "with",
    "you",
    "your",
}

DEFLECTION_PHRASES = (
    "another team",
    "as previously stated",
    "cannot comment",
    "can't comment",
    "check the faq",
    "follow up later",
    "not in my queue",
    "please refer to",
    "someone will reach out",
    "we are looking into it",
)

DIRECT_ANSWER_PHRASES = (
    "because",
    "here are the steps",
    "i can confirm",
    "i checked",
    "i fixed",
    "the reason is",
    "the steps are",
    "we can",
    "we have",
    "we shipped",
    "you can",
    "you need to",
    "you should",
)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS]


def _messages_by_role(parsed_conversation: dict[str, Any], role: str) -> list[str]:
    return [
        message["text"]
        for message in parsed_conversation.get("messages", [])
        if message.get("role") == role and message.get("text")
    ]


def _lexicon_ratio(texts: list[str], lexicon: set[str]) -> float:
    tokens = [token for text in texts for token in tokenize(text)]
    if not tokens:
        return 0.0
    hits = sum(1 for token in tokens if token in lexicon)
    return round(hits / len(tokens), 4)


def positive_language_ratio(parsed_conversation: dict[str, Any]) -> float:
    texts = [message["text"] for message in parsed_conversation.get("messages", [])]
    return _lexicon_ratio(texts, LOUGHRAN_MCDONALD_POSITIVE)


def negative_language_ratio(parsed_conversation: dict[str, Any]) -> float:
    texts = [message["text"] for message in parsed_conversation.get("messages", [])]
    return _lexicon_ratio(texts, LOUGHRAN_MCDONALD_NEGATIVE)


def hedging_ratio(parsed_conversation: dict[str, Any]) -> float:
    agent_texts = _messages_by_role(parsed_conversation, "agent")
    return _lexicon_ratio(agent_texts, HEDGING_TERMS)


def verbosity_ratio(parsed_conversation: dict[str, Any]) -> float:
    customer_tokens = sum(len(tokenize(text)) for text in _messages_by_role(parsed_conversation, "customer"))
    agent_tokens = sum(len(tokenize(text)) for text in _messages_by_role(parsed_conversation, "agent"))
    total = customer_tokens + agent_tokens
    if total == 0:
        return 0.0
    return round(agent_tokens / total, 4)


def qa_deflection_rate(parsed_conversation: dict[str, Any]) -> float:
    pair_scores = _pair_diagnostics(parsed_conversation)
    if not pair_scores:
        return 0.0
    deflections = sum(1 for item in pair_scores if item["is_deflection"])
    return round(deflections / len(pair_scores), 4)


def directness_score(parsed_conversation: dict[str, Any]) -> float:
    pair_scores = _pair_diagnostics(parsed_conversation)
    if not pair_scores:
        return 0.0
    mean_score = sum(item["directness"] for item in pair_scores) / len(pair_scores)
    return round(_clamp(mean_score), 4)


def _term_frequency(tokens: list[str]) -> Counter[str]:
    return Counter(tokens)


def _tfidf_vectors(texts: list[str]) -> list[dict[str, float]]:
    token_lists = [_content_tokens(text) for text in texts]
    if not token_lists:
        return []
    document_count = len(token_lists)
    document_frequency: Counter[str] = Counter()
    for tokens in token_lists:
        document_frequency.update(set(tokens))

    vectors: list[dict[str, float]] = []
    for tokens in token_lists:
        if not tokens:
            vectors.append({})
            continue
        tf = _term_frequency(tokens)
        max_tf = max(tf.values())
        vector: dict[str, float] = {}
        for token, count in tf.items():
            idf = math.log((1 + document_count) / (1 + document_frequency[token])) + 1.0
            vector[token] = (count / max_tf) * idf
        norm = math.sqrt(sum(value * value for value in vector.values()))
        if norm:
            vector = {token: value / norm for token, value in vector.items()}
        vectors.append(vector)
    return vectors


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    overlap = set(left).intersection(right)
    return sum(left[token] * right[token] for token in overlap)


def consistency_score(parsed_conversation: dict[str, Any]) -> float:
    similarities: list[float] = []
    for pair in parsed_conversation.get("pairs", []):
        customer = pair.get("customer")
        agent = pair.get("agent")
        if not customer or not agent:
            continue
        texts = [customer.get("text", ""), agent.get("text", "")]
        left, right = _tfidf_vectors(texts)
        similarities.append(_cosine_similarity(left, right))
    if not similarities:
        return 1.0
    raw_mean = sum(similarities) / len(similarities)
    scaled_mean = min(1.0, raw_mean * 2.5)
    return round(_clamp(scaled_mean), 4)


def qa_score(parsed_conversation: dict[str, Any]) -> float:
    positive = positive_language_ratio(parsed_conversation)
    negative = negative_language_ratio(parsed_conversation)
    hedging = hedging_ratio(parsed_conversation)
    directness = directness_score(parsed_conversation)
    deflection = qa_deflection_rate(parsed_conversation)
    consistency = consistency_score(parsed_conversation)
    verbosity = verbosity_ratio(parsed_conversation)
    verbosity_balance = 1.0 - abs(0.5 - verbosity) * 2.0

    score = (
        0.30 * directness
        + 0.20 * (1.0 - deflection)
        + 0.15 * consistency
        + 0.10 * (1.0 - negative)
        + 0.10 * positive
        + 0.10 * (1.0 - hedging)
        + 0.05 * _clamp(verbosity_balance)
    )
    return round(_clamp(score), 4)


def customer_negative_ratio(parsed_conversation: dict[str, Any]) -> float:
    return _lexicon_ratio(_messages_by_role(parsed_conversation, "customer"), LOUGHRAN_MCDONALD_NEGATIVE)


def agent_message_count(parsed_conversation: dict[str, Any]) -> int:
    return len(_messages_by_role(parsed_conversation, "agent"))


def _pair_diagnostics(parsed_conversation: dict[str, Any]) -> list[dict[str, float | bool]]:
    diagnostics: list[dict[str, float | bool]] = []
    for pair in parsed_conversation.get("pairs", []):
        customer = pair.get("customer")
        if not customer or not customer.get("text"):
            continue

        agent = pair.get("agent")
        if not agent or not agent.get("text"):
            diagnostics.append({"directness": 0.0, "is_deflection": True})
            continue

        customer_text = customer["text"].lower()
        agent_text = agent["text"].lower()
        customer_terms = set(_content_tokens(customer_text))
        agent_terms = set(_content_tokens(agent_text))
        overlap = (len(customer_terms & agent_terms) / len(customer_terms)) if customer_terms else 0.0
        hedge_penalty = _lexicon_ratio([agent_text], HEDGING_TERMS) * 3.0
        direct_cue = 1.0 if any(phrase in agent_text for phrase in DIRECT_ANSWER_PHRASES) else 0.0
        deflection_phrase = any(phrase in agent_text for phrase in DEFLECTION_PHRASES)
        low_coverage = overlap < 0.15 and direct_cue == 0.0
        is_deflection = bool(deflection_phrase or low_coverage)
        score = (0.60 * overlap) + (0.25 * direct_cue) + (0.15 * (1.0 - min(1.0, hedge_penalty)))
        if deflection_phrase:
            score -= 0.35
        diagnostics.append({"directness": _clamp(score), "is_deflection": is_deflection})
    return diagnostics


def compute_feature_set(parsed_conversation: dict[str, Any]) -> dict[str, float]:
    return {
        "positive_language_ratio": positive_language_ratio(parsed_conversation),
        "negative_language_ratio": negative_language_ratio(parsed_conversation),
        "hedging_ratio": hedging_ratio(parsed_conversation),
        "directness_score": directness_score(parsed_conversation),
        "qa_deflection_rate": qa_deflection_rate(parsed_conversation),
        "verbosity_ratio": verbosity_ratio(parsed_conversation),
        "consistency_score": consistency_score(parsed_conversation),
        "qa_score": qa_score(parsed_conversation),
    }
