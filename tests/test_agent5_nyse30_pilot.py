from __future__ import annotations

import yaml

from signal_engine.agent5_acquisition import build_nyse_30_targets, validate_nyse_30_targets


def test_nyse30_pilot_is_metadata_only_and_exact_ticker_set() -> None:
    rows = build_nyse_30_targets()
    assert [row["ticker"] for row in rows] == [
        "JPM",
        "WMT",
        "HD",
        "JNJ",
        "XOM",
        "BAC",
        "GS",
        "MS",
        "BLK",
        "AXP",
        "CRM",
        "ORCL",
        "IBM",
        "NOW",
        "NET",
        "LLY",
        "MRK",
        "PFE",
        "UNH",
        "CVS",
        "BA",
        "CAT",
        "DE",
        "GE",
        "HON",
        "KO",
        "MCD",
        "NKE",
        "DIS",
        "T",
    ]
    assert not validate_nyse_30_targets(rows)
    assert all(row["raw_transcript_allowed"] is False for row in rows)
    assert all(row["raw_audio_allowed"] is False for row in rows)
    assert all(row["raw_video_allowed"] is False for row in rows)
    assert all(row["commit_allowed"] is False for row in rows)
    assert all(row["training_allowed"] is False for row in rows)
    assert all(row["eval_allowed"] is False for row in rows)


def test_committed_nyse30_config_validates() -> None:
    payload = yaml.safe_load(open("configs/nyse_30_pilot_targets.yml", encoding="utf-8"))
    rows = payload["targets"]
    assert len(rows) == 30
    assert not validate_nyse_30_targets(rows)


def test_unknown_rights_blocks_raw_ingest() -> None:
    rows = build_nyse_30_targets()
    rows[0]["raw_transcript_allowed"] = True
    errors = validate_nyse_30_targets(rows)
    assert any("unknown/restricted rights cannot allow raw ingest" in error for error in errors)
