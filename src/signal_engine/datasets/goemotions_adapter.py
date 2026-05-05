from __future__ import annotations

from pathlib import Path

from signal_engine.datasets.generic_csv_adapter import load_generic_csv

LABEL_MAP = {
    "admiration": "opportunity_commitment",
    "approval": "opportunity_commitment",
    "optimism": "opportunity_commitment",
    "confusion": "uncertainty_hedging",
    "fear": "risk_friction",
    "disappointment": "risk_friction",
    "neutral": "neutral",
}


def load_goemotions_local(path: str | Path) -> list[dict[str, str]]:
    """Load a manually downloaded GoEmotions CSV; never downloads data."""
    rows = load_generic_csv(path, text_column="text", label_column="label")
    mapped: list[dict[str, str]] = []
    for row in rows:
        external = str(row["external_label"]).lower()
        mapped.append(
            {
                "text": str(row["text"]),
                "external_label": external,
                "mapped_signal_label": LABEL_MAP.get(external, "unmapped"),
                "source_path": str(row["source_path"]),
            }
        )
    return mapped
