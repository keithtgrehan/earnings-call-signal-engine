from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.model_sidecars.benchmark import write_benchmark_outputs
from earnings_call_sentiment.model_sidecars.runner import benchmark_model_sidecars
import earnings_call_sentiment.model_sidecars.runner as runner


def test_benchmark_model_sidecars_records_cold_and_warm_runs(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def _fake_run_model_sidecars(**kwargs):
        calls.append(kwargs)
        return {
            "cases": [
                {
                    "case_id": "synthetic_case",
                    "output_root": "/tmp/outputs/synthetic_case/model_sidecars",
                    "sampling": {"chunks": {"selected_count": 2}},
                    "models": {
                        "finbert_tone": {
                            "runtime_s": 1.2,
                            "prewarm_runtime_s": 0.1,
                            "device": "cpu",
                            "unit_results": {
                                "chunks": {
                                    "selected_count": 2,
                                    "runtime_s": 0.5,
                                    "items_per_s": 4.0,
                                    "process_peak_rss_bytes": 123456,
                                }
                            },
                        }
                    },
                }
            ]
        }

    monkeypatch.setattr(runner, "run_model_sidecars", _fake_run_model_sidecars)

    payload = benchmark_model_sidecars(
        case_ids=["synthetic_case"],
        model_names=["finbert_tone"],
        unit_types=["chunks"],
        run_mode="both",
    )

    assert [call["prewarm_models"] for call in calls] == [False, True]
    assert payload["run_mode"] == "both"
    assert len(payload["runs"]) == 2


def test_write_benchmark_outputs_writes_json_and_markdown(tmp_path: Path) -> None:
    payload = {
        "run_mode": "warm",
        "runs": [
            {
                "run_label": "warm",
                "payload": {
                    "cases": [
                        {
                            "case_id": "synthetic_case",
                            "output_root": str(tmp_path / "outputs" / "synthetic_case" / "model_sidecars"),
                            "sampling": {"chunks": {"selected_count": 2}},
                            "models": {
                                "finbert_tone": {
                                    "runtime_s": 1.2,
                                    "prewarm_runtime_s": 0.1,
                                    "device": "cpu",
                                    "unit_results": {
                                        "chunks": {
                                            "selected_count": 2,
                                            "runtime_s": 0.5,
                                            "items_per_s": 4.0,
                                            "process_peak_rss_bytes": 123456,
                                        }
                                    },
                                }
                            },
                        }
                    ]
                },
            }
        ],
        "notes": ["Peak memory is approximate process-level RSS where available."],
    }

    artifacts = write_benchmark_outputs(payload, output_root=tmp_path / "outputs")

    json_payload = json.loads(
        artifacts["synthetic_case"]["json_path"].read_text(encoding="utf-8")
    )
    assert json_payload["case_id"] == "synthetic_case"
    assert artifacts["synthetic_case"]["md_path"].exists()
