from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script_module(name: str, relative_path: str):
    script_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_media_support_readiness_downstream_summary_tracks_unscored_rows(tmp_path: Path) -> None:
    module = _load_script_module(
        "check_media_support_readiness_script",
        "scripts/check_media_support_readiness.py",
    )
    cases_path = tmp_path / "data" / "media_support_eval" / "downstream_decision_eval_cases.csv"
    cases_path.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {"case_id": "call01", "target_support_direction": "supportive"},
            {"case_id": "call02", "target_support_direction": ""},
            {"case_id": "call03", "target_support_direction": ""},
        ]
    ).to_csv(cases_path, index=False)

    summary = module._downstream_case_summary(tmp_path)

    assert summary["case_rows"] == 3
    assert summary["support_target_rows"] == 1
    assert summary["case_rows_without_support_targets"] == 2
    assert "Only 1 of 3 downstream cases" in summary["readiness_note"]


def test_compare_multimodal_support_slice_script_writes_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_script_module(
        "compare_multimodal_support_slice_script",
        "scripts/compare_multimodal_support_slice.py",
    )

    cases_path = tmp_path / "data" / "media_support_eval" / "downstream_decision_eval_cases.csv"
    cases_path.parent.mkdir(parents=True)
    pd.DataFrame([{"case_id": "call01"}]).to_csv(cases_path, index=False)

    def fake_evaluate(cases: pd.DataFrame):
        return (
            pd.DataFrame([{"case_id": str(cases.iloc[0]["case_id"]), "current_direction": "neutral"}]),
            {"case_count": int(len(cases)), "case_count_with_support_targets": 0},
        )

    monkeypatch.setattr(module, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(module, "evaluate_downstream_decision_cases", fake_evaluate)

    result = module.main([])

    summary_path = tmp_path / "outputs" / "media_support_eval" / "downstream_decision_comparison.json"
    rows_path = tmp_path / "outputs" / "media_support_eval" / "downstream_decision_comparison_rows.csv"

    assert result == 0
    assert summary_path.exists()
    assert rows_path.exists()
    written_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert written_summary["case_count"] == 1
    assert written_summary["cases_path"] == str(cases_path)
    assert "downstream_decision_comparison.json" in capsys.readouterr().out
