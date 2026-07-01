from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "architecture" / "cross_domain_safe_nlp_architecture.md"

REQUIRED_LAYERS = [
    "rights/consent gate",
    "PII minimization",
    "dataset registry",
    "deterministic baseline",
    "candidate classifier",
    "evidence object store",
    "retrieval layer",
    "BYOK reviewer layer",
    "multimodal metadata layer",
    "evaluation gates",
    "output safety guardrails",
]


def test_architecture_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_architecture_doc_contains_every_required_layer() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    for layer in REQUIRED_LAYERS:
        assert layer in text


def test_architecture_doc_contains_required_phrases() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "deterministic baseline",
        "evidence object store",
        "BYOK reviewer",
        "consent gate",
        "PII minimization",
    ]:
        assert phrase in text
