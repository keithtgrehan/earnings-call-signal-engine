from __future__ import annotations

from tools.verify_vz_2024_q4_pair import FULL_TRANSCRIPT_URL, PREPARED_AUDIO_URL, PREPARED_TRANSCRIPT_URL, PAIR_MANIFEST_FIELDS


def test_vz_pair_uses_direct_verizon_assets() -> None:
    assert FULL_TRANSCRIPT_URL.startswith("https://www.verizon.com/")
    assert PREPARED_TRANSCRIPT_URL.startswith("https://www.verizon.com/")
    assert PREPARED_AUDIO_URL.endswith(".mp3")


def test_vz_pair_manifest_records_partial_relation() -> None:
    assert "source_relation" in PAIR_MANIFEST_FIELDS
    assert "pair_status" in PAIR_MANIFEST_FIELDS
    assert "review_required" in PAIR_MANIFEST_FIELDS
