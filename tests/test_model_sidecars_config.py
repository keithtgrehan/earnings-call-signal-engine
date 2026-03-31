from __future__ import annotations

from pathlib import Path

import pytest

from earnings_call_sentiment.model_sidecars.config import load_zero_shot_label_groups


def test_load_zero_shot_label_groups_reads_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "labels.yaml"
    config_path.write_text(
        "management_stance:\n"
        "  - reassuring\n"
        "  - cautious\n"
        "qa_dynamics:\n"
        "  - direct answer\n",
        encoding="utf-8",
    )

    payload = load_zero_shot_label_groups(config_path)

    assert payload["management_stance"] == ["reassuring", "cautious"]
    assert payload["qa_dynamics"] == ["direct answer"]


def test_load_zero_shot_label_groups_rejects_invalid_shape(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("- not-a-mapping\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="non-empty mapping"):
        load_zero_shot_label_groups(config_path)
