from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import text_features as base_text_features

LM_CATEGORY_NAMES: tuple[str, ...] = (
    "negative",
    "positive",
    "uncertainty",
    "litigious",
    "modal",
    "constraining",
)

DEFAULT_LEXICON_PATH = Path(__file__).resolve().parents[3] / "data" / "lexicons" / "loughran_mcdonald_lexicon.json"


def load_loughran_mcdonald_lexicon(path: Path | None = None) -> dict[str, list[str]]:
    lexicon_path = path or DEFAULT_LEXICON_PATH
    if not lexicon_path.exists():
        return {category: [] for category in LM_CATEGORY_NAMES}
    payload = json.loads(lexicon_path.read_text(encoding="utf-8"))
    lexicon = payload.get("lexicon", payload)
    return {
        category: sorted({str(term).lower() for term in lexicon.get(category, []) if str(term).strip()})
        for category in LM_CATEGORY_NAMES
    }


def match_loughran_mcdonald_terms(
    text: str,
    *,
    lexicon: dict[str, list[str]] | None = None,
    limit_per_category: int = 8,
) -> dict[str, list[str]]:
    normalized = lexicon or load_loughran_mcdonald_lexicon()
    matches: dict[str, list[str]] = {}
    for category in LM_CATEGORY_NAMES:
        terms = normalized.get(category, [])
        matched = [term for term in terms if base_text_features.term_found(text, term)]
        matches[category] = matched[:limit_per_category]
    return matches


def summarize_lm_matches(matches: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "matched_categories": [category for category, terms in matches.items() if terms],
        "matched_term_count": sum(len(terms) for terms in matches.values()),
    }
