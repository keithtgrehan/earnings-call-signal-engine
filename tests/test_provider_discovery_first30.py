from __future__ import annotations

import csv
from pathlib import Path

from tools.provider_discovery_first30 import provider_discovery_first30


def test_provider_discovery_writes_metadata_only_outputs(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.csv"
    candidates.write_text(
        "case_id,ticker,fiscal_year,fiscal_quarter,control_fixture\n"
        "jpm_2025_q4,JPM,2025,Q4,false\n",
        encoding="utf-8",
    )
    assets = tmp_path / "provider_assets.csv"
    gaps = tmp_path / "provider_gaps.csv"
    acquisition = tmp_path / "provider_first30_asset_candidates.csv"
    summary = provider_discovery_first30(candidate_path=candidates, assets_out=assets, gaps_out=gaps, acquisition_candidates_out=acquisition)
    assert summary["raw_provider_pull_attempted"] is False
    assert summary["asset_rows"] >= 1
    with assets.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    assert rows
    assert all(row["training_allowed"] == "false" for row in rows)
    assert any(row["discovery_status"] == "NOT_CONFIGURED" for row in rows)
    assert gaps.exists()
    assert acquisition.exists()
