from __future__ import annotations

import json

from earnings_call_sentiment import cli


def test_build_sidecars_parser_parses_expected_arguments() -> None:
    parser = cli.build_sidecars_parser()
    args = parser.parse_args(
        [
            "--case-id",
            "nvidia_q4_fy2024",
            "--models",
            "finbert_tone",
            "mpnet_embeddings",
            "--units",
            "chunks",
            "guidance_spans",
            "--zero-shot-label-config",
            "configs/model_eval/zero_shot_labels.finance.yaml",
            "--sample-size",
            "4",
            "--sample-strategy",
            "random",
            "--seed",
            "13",
        ]
    )

    assert args.case_id == ["nvidia_q4_fy2024"]
    assert args.models == ["finbert_tone", "mpnet_embeddings"]
    assert args.units == ["chunks", "guidance_spans"]
    assert args.sample_size == 4
    assert args.sample_strategy == "random"
    assert args.seed == 13


def test_main_routes_sidecars_subcommand(monkeypatch, capsys) -> None:
    def _fake_run_model_sidecars(**kwargs):
        assert kwargs["case_ids"] == ["nvidia_q4_fy2024"]
        assert kwargs["model_names"] == ["finbert_tone"]
        assert kwargs["unit_types"] == ["chunks"]
        return {"cases": [{"case_id": "nvidia_q4_fy2024"}]}

    monkeypatch.setattr(cli, "run_model_sidecars", _fake_run_model_sidecars)

    exit_code = cli.main(
        [
            "sidecars",
            "--case-id",
            "nvidia_q4_fy2024",
            "--models",
            "finbert_tone",
            "--units",
            "chunks",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["cases"][0]["case_id"] == "nvidia_q4_fy2024"


def test_main_routes_sidecars_prewarm(monkeypatch, capsys) -> None:
    def _fake_prewarm_model_sidecars(**kwargs):
        assert kwargs["model_names"] == ["finbert_tone"]
        assert kwargs["device"] == "cpu"
        return {
            "requested_models": ["finbert_tone"],
            "warmed_models": ["finbert_tone"],
            "failed_models": [],
            "results": [],
        }

    monkeypatch.setattr(cli, "prewarm_model_sidecars", _fake_prewarm_model_sidecars)

    exit_code = cli.main(
        [
            "sidecars-prewarm",
            "--models",
            "finbert_tone",
            "--device",
            "cpu",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["warmed_models"] == ["finbert_tone"]
