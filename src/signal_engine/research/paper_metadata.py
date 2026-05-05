from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_CATEGORIES = {
    "sequence_models",
    "attention_transformers",
    "representation_learning",
    "compression_mdl_complexity",
    "vision_multimodal",
    "speech_audio",
    "scaling_systems",
    "reasoning_memory",
    "graph_relational_learning",
    "evaluation_theory",
}

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_METADATA_PATH = REPO_ROOT / "data" / "research" / "ilya_reading_list" / "papers_metadata.json"


def load_papers(metadata_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load Ilya reading-list paper metadata from the repository JSON asset."""
    path = Path(metadata_path) if metadata_path is not None else DEFAULT_METADATA_PATH
    with path.open(encoding="utf-8") as file:
        papers = json.load(file)
    if not isinstance(papers, list):
        raise ValueError(f"Expected a list of papers in {path}")
    return papers


def get_paper(paper_id: str, metadata_path: str | Path | None = None) -> dict[str, Any]:
    """Return one paper by id."""
    for paper in load_papers(metadata_path):
        if paper.get("id") == paper_id:
            return paper
    raise KeyError(f"Unknown paper id: {paper_id}")


def filter_by_category(category: str, metadata_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return papers for a valid primary category."""
    if category not in VALID_CATEGORIES:
        valid = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"Unknown category {category!r}. Valid categories: {valid}")
    return [paper for paper in load_papers(metadata_path) if paper.get("category") == category]


def signal_engine_relevance(paper_id: str, metadata_path: str | Path | None = None) -> list[str]:
    """Return distilled Signal Engine relevance notes for one paper."""
    paper = get_paper(paper_id, metadata_path)
    relevance = paper.get("signal_engine_relevance", [])
    if not isinstance(relevance, list):
        raise ValueError(f"Paper {paper_id!r} has invalid signal_engine_relevance")
    return relevance
