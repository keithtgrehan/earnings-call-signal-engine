from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from signal_engine.research.paper_metadata import REPO_ROOT, load_papers

EXTRACTED_DIR = REPO_ROOT / "data" / "research" / "ilya_reading_list" / "extracted"
BRIEFS_DIR = REPO_ROOT / "docs" / "research" / "ilya_reading_list" / "papers"


def _flatten_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _flatten_values(item)


def _paper_text(paper: dict[str, Any]) -> str:
    fields = [
        "id",
        "title",
        "authors",
        "category",
        "core_concepts",
        "signal_engine_relevance",
        "future_features",
        "core_idea",
        "historical_importance",
        "beginner_takeaway",
        "possible_evaluation_ideas",
        "risks_limitations",
    ]
    text_parts = [text for field in fields for text in _flatten_values(paper.get(field, ""))]
    extracted_path = EXTRACTED_DIR / f"{paper.get('id')}.json"
    if extracted_path.exists():
        text_parts.append(extracted_path.read_text(encoding="utf-8"))
    brief_paths = sorted(BRIEFS_DIR.glob(f"*_{paper.get('id')}.md"))
    if paper.get("id") == "stanford_cs231n_convolutional_neural_networks":
        brief_paths = [BRIEFS_DIR / "26_cs231n.md"]
    for path in brief_paths:
        if path.exists():
            text_parts.append(path.read_text(encoding="utf-8"))
    return " ".join(text_parts).lower()


def _tokens(query: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[a-zA-Z0-9_]+", query) if token.strip()]
    expanded = list(tokens)
    if "rnn" in tokens:
        expanded.extend(["recurrent", "lstm"])
    if "multimodal" in tokens:
        expanded.extend(["audio", "speech", "vision", "video", "prosody"])
    if "compression" in tokens:
        expanded.extend(["mdl", "description", "kolmogorov"])
    if {"signal", "engine"} <= set(tokens):
        expanded.extend(["transcript", "evidence", "retrieval", "roadmap", "evaluation"])
    return expanded


def search_papers(query: str, *, limit: int | None = None) -> list[dict[str, Any]]:
    """Run a dependency-free keyword search over paper metadata."""
    tokens = _tokens(query)
    if not tokens:
        return []

    scored: list[tuple[int, dict[str, Any]]] = []
    for paper in load_papers():
        text = _paper_text(paper)
        score = sum(text.count(token) for token in tokens)
        if score:
            # Title and id hits usually reflect clearer intent than body hits.
            title_id = f"{paper.get('id', '')} {paper.get('title', '')}".lower()
            score += 3 * sum(token in title_id for token in tokens)
            scored.append((score, paper))

    scored.sort(key=lambda item: (-item[0], item[1].get("year") or 9999, item[1].get("title", "")))
    papers = [paper for _, paper in scored]
    return papers if limit is None else papers[:limit]
