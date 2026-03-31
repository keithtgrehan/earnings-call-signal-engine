from __future__ import annotations

from pathlib import Path

import pytest

from earnings_call_sentiment.model_sidecars.config import load_sidecar_manifest


def test_load_sidecar_manifest_reads_expected_fields(tmp_path: Path) -> None:
    manifest_path = tmp_path / "cpu_smoke.yaml"
    manifest_path.write_text(
        "name: CPU Smoke 5\n"
        "case_ids:\n"
        "  - nvidia_q4_fy2024\n"
        "models:\n"
        "  - finbert_tone\n"
        "  - deberta_zero_shot\n"
        "units:\n"
        "  - chunks\n"
        "device_expectation: cpu\n"
        "batch_size: 2\n"
        "sample_size: 3\n"
        "sample_strategy: random\n"
        "seed: 11\n"
        "output_root: ./outputs\n",
        encoding="utf-8",
    )

    payload = load_sidecar_manifest(manifest_path)

    assert payload["name"] == "CPU Smoke 5"
    assert payload["case_ids"] == ["nvidia_q4_fy2024"]
    assert payload["models"] == ["finbert_tone", "deberta_zero_shot"]
    assert payload["units"] == ["chunks"]
    assert payload["device_expectation"] == "cpu"
    assert payload["batch_size"] == 2
    assert payload["sample_size"] == 3
    assert payload["sample_strategy"] == "random"


def test_load_sidecar_manifest_rejects_missing_lists(tmp_path: Path) -> None:
    manifest_path = tmp_path / "invalid.yaml"
    manifest_path.write_text("name: invalid\nmodels: [finbert_tone]\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="case_ids"):
        load_sidecar_manifest(manifest_path)
