from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "docs" / "research" / "multimodal_affective_cue_research.md",
    ROOT / "docs" / "multimodal_audit_layer.md",
    ROOT / "docs" / "legal" / "multimodal_rights_and_ai_act_guardrails.md",
]


def test_multimodal_docs_contain_required_guardrails() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)

    for phrase in [
        "Transcript remains canonical",
        "reviewer-support only",
        "no deception detection",
        "no mental-health diagnosis",
        "no biometric identity inference",
        "rights-cleared",
        "flagged windows only",
    ]:
        assert phrase in combined
