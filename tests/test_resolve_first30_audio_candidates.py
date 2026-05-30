from __future__ import annotations

from tools.resolve_first30_audio_candidates import is_direct_audio_url


def test_direct_audio_url_accepts_company_mp3_and_blocks_platforms() -> None:
    assert is_direct_audio_url("https://www.verizon.com/about/sites/default/files/1Q25_EarningsCall_PreparedCommentary.mp3")
    assert not is_direct_audio_url("https://soundcloud.com/verizon-communications/vz-1q25-earnings")
    assert not is_direct_audio_url("https://youtube.com/watch?v=abc")
