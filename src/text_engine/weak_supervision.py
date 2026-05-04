from __future__ import annotations

from typing import Any

from signal_engine.signal_baseline import SIGNAL_FAMILY_LABELS, predict_deterministic_signal_family

ABSTAIN = -1
LABEL_TO_INT = {label: index for index, label in enumerate(SIGNAL_FAMILY_LABELS)}
INT_TO_LABEL = {index: label for label, index in LABEL_TO_INT.items()}


def weak_label_segment(text: str, *, domain: str) -> dict[str, Any]:
    rule_prediction = predict_deterministic_signal_family(text, domain=domain)
    label = str(rule_prediction["label"])
    label_id = LABEL_TO_INT.get(label, ABSTAIN)
    return {
        "label": label if label_id != ABSTAIN else "neutral",
        "label_id": label_id,
        "method": "snorkel_compatible_labeling_functions",
        "snorkel_available": _snorkel_available(),
        "evidence_terms": rule_prediction.get("evidence_terms", []),
        "reason": rule_prediction.get("reason", ""),
    }


def _snorkel_available() -> bool:
    try:
        import snorkel  # noqa: F401
    except ImportError:
        return False
    return True
