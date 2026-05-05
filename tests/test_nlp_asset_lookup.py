from __future__ import annotations

from signal_engine.nlp_assets.lookup import (
    filter_by_category,
    filter_by_download_status,
    filter_by_priority,
    find_by_signal_engine_area,
)


def _ids(assets: list[dict]) -> set[str]:
    return {asset["id"] for asset in assets}


def test_lookup_by_category() -> None:
    assert "financial_phrasebank" in _ids(filter_by_category("finance"))
    assert "goemotions" in _ids(filter_by_category("sentiment_emotion"))
    assert "rank_bm25" in _ids(filter_by_category("embeddings_retrieval_tools"))
    assert "faster_whisper" in _ids(filter_by_category("audio_asr_prosody"))
    assert "cmu_mosei" in _ids(filter_by_category("video_multimodal"))


def test_lookup_by_download_status_and_priority() -> None:
    assert "sec_company_tickers" in _ids(filter_by_download_status("downloaded"))
    assert "loughran_mcdonald_lexicon" in _ids(filter_by_download_status("manual_required"))
    assert "financial_phrasebank" in _ids(filter_by_priority("high"))


def test_lookup_by_signal_engine_area() -> None:
    assert "loughran_mcdonald_lexicon" in _ids(find_by_signal_engine_area("weak_labeling"))
    assert "goemotions" in _ids(find_by_signal_engine_area("emotion"))
    assert "rank_bm25" in _ids(find_by_signal_engine_area("retrieval"))
    assert "faster_whisper" in _ids(find_by_signal_engine_area("audio"))
    assert "cmu_mosei" in _ids(find_by_signal_engine_area("multimodal"))
