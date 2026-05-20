from __future__ import annotations

import csv
from pathlib import Path

from signal_engine.datasets.financial_phrasebank_adapter import load_financial_phrasebank_local
from signal_engine.datasets.goemotions_adapter import load_goemotions_local
from signal_engine.datasets.sec_metadata_adapter import normalize_sec_metadata_row


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_financial_phrasebank_mapping_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "phrasebank.csv"
    write_csv(source, [{"text": "Margins improved.", "label": "positive"}, {"text": "Demand weakened.", "label": "negative"}])

    rows = load_financial_phrasebank_local(source)

    assert [row["mapped_signal_label"] for row in rows] == ["opportunity_commitment", "risk_friction"]
    assert all(row["source_path"] == str(source) for row in rows)


def test_goemotions_mapping_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "goemotions.csv"
    write_csv(source, [{"text": "I am confused by the update.", "label": "confusion"}, {"text": "That looks fine.", "label": "neutral"}])

    rows = load_goemotions_local(source)

    assert [row["mapped_signal_label"] for row in rows] == ["uncertainty_hedging", "neutral"]
    assert rows[0]["external_label"] == "confusion"


def test_sec_metadata_normalization_preserves_metadata_only() -> None:
    row = normalize_sec_metadata_row(
        {
            "accession": "0000000000-26-000001",
            "ticker": "nvda",
            "form": "8-k",
            "filing_date": "2026-02-20",
            "url": "https://www.sec.gov/example",
        }
    )

    assert row == {
        "accession_number": "0000000000-26-000001",
        "ticker": "NVDA",
        "filing_type": "8-K",
        "filed_at": "2026-02-20",
        "source_url": "https://www.sec.gov/example",
        "source_type": "sec_metadata",
    }
