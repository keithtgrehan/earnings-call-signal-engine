from __future__ import annotations

import json
from pathlib import Path

import pytest

from earnings_call_sentiment.nlp_sidecars.config import load_zero_shot_label_groups


def test_load_zero_shot_label_groups_from_json(tmp_path: Path) -> None:
    path = tmp_path / "labels.json"
    path.write_text(
        json.dumps(
            {
                "tone": ["positive", "neutral", "negative"],
                "qa_answer_style": ["direct answer", "qualified answer"],
            }
        ),
        encoding="utf-8",
    )

    groups = load_zero_shot_label_groups(path)

    assert groups["tone"] == ["positive", "neutral", "negative"]
    assert groups["qa_answer_style"] == ["direct answer", "qualified answer"]


def test_load_zero_shot_label_groups_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Zero-shot label config was not found"):
        load_zero_shot_label_groups(tmp_path / "missing.json")
