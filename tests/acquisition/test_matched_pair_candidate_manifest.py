from __future__ import annotations

from pathlib import Path

from scripts.validate_matched_pair_candidates import validate_file


def test_matched_pair_manifest_validates() -> None:
    summary = validate_file(Path("data/acquisition/matched_pair_candidates.csv"))
    assert summary["rows"] >= 2
    assert summary["errors"] == []


def test_vz_candidate_is_approval_gated() -> None:
    rows = Path("data/acquisition/matched_pair_candidates.csv").read_text(encoding="utf-8").splitlines()
    vz = next(row for row in rows if row.startswith("mp_vz_2024_q4,"))
    assert "prepared_audio_vs_full_transcript" in vz
    assert ",true,prepared_earnings_audio,true,,true,false,false,false,false," in vz
