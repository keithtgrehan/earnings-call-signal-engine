from __future__ import annotations

from signal_engine.chunking.qa_pairer import qa_pair_spans


def test_qa_pairer_pairs_questioner_to_management() -> None:
    turns = [
        {"turn_id": "turn_0001", "speaker_role": "analyst", "start_char": 1, "end_char": 10},
        {"turn_id": "turn_0002", "speaker_role": "management", "start_char": 11, "end_char": 20},
    ]

    pairs = qa_pair_spans(turns)

    assert pairs == [{"qa_pair_id": "qa_pair_0001", "question_turn_id": "turn_0001", "answer_turn_id": "turn_0002", "start_char": 1, "end_char": 20}]
