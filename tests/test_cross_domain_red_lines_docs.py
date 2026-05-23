from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "policies" / "red_lines_cross_domain_nlp.md"


def test_red_lines_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_red_lines_doc_contains_mandatory_forbidden_outputs() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "this person is lying",
        "this person loves you",
        "emotional vulnerability scoring",
        "workplace/education emotion inference",
        "biometric identity inference",
        "sensitive trait inference",
        "trading signal claims",
        "source-rights bypass",
        "relationship manipulation suggestions",
        "unsupported statistical significance",
        "deception detection",
        "mental-health diagnosis",
        "universal emotion truth claims",
    ]:
        assert phrase in text


def test_red_lines_doc_contains_required_safe_language() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    for phrase in [
        "observable cues only",
        "candidate/reviewer-support only",
        "no source-rights bypass",
    ]:
        assert phrase in text
