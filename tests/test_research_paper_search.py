from __future__ import annotations

from signal_engine.research.search import search_papers


def _ids(query: str) -> set[str]:
    return {paper["id"] for paper in search_papers(query)}


def test_search_attention_returns_transformer_and_pointer_papers() -> None:
    ids = _ids("attention")
    assert "attention_is_all_you_need" in ids
    assert "pointer_networks" in ids


def test_search_rnn_returns_sequence_papers() -> None:
    ids = _ids("RNN")
    assert "unreasonable_effectiveness_rnns" in ids
    assert "rnn_regularization" in ids


def test_search_scaling_returns_scaling_papers() -> None:
    ids = _ids("scaling")
    assert "scaling_laws_neural_language_models" in ids
    assert "gpipe_scaling_microbatch_pipeline_parallelism" in ids


def test_search_compression_returns_mdl_complexity_papers() -> None:
    ids = _ids("compression")
    assert "tutorial_minimum_description_length_principle" in ids
    assert "kolmogorov_complexity_algorithmic_randomness" in ids


def test_search_speech_and_multimodal_return_expected_papers() -> None:
    assert "deep_speech_2_end_to_end_speech_recognition" in _ids("speech")
    multimodal_ids = _ids("multimodal")
    assert "stanford_cs231n_convolutional_neural_networks" in multimodal_ids
    assert "deep_speech_2_end_to_end_speech_recognition" in multimodal_ids


def test_search_signal_engine_returns_scoped_metadata() -> None:
    ids = _ids("Signal Engine")
    assert "attention_is_all_you_need" in ids
    assert "scaling_laws_neural_language_models" in ids
