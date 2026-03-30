from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_nlp_sidecars.py"
    spec = importlib.util.spec_from_file_location("run_nlp_sidecars_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_nlp_sidecars_script_compare_invokes_summary_writer(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_script_module()
    called = {}

    def fake_write_case_evaluation_summary(*, case_id, output_root):
        called["case_id"] = case_id
        called["output_root"] = output_root
        return {
            "runtime_summary": tmp_path / "runtime_summary.json",
            "comparison_summary": tmp_path / "comparison_summary.json",
            "comparison_markdown": tmp_path / "comparison_summary.md",
        }

    monkeypatch.setattr(module, "write_case_evaluation_summary", fake_write_case_evaluation_summary)

    result = module.main(["compare", "--case-id", "demo_case", "--output-root", str(tmp_path / "outputs")])

    assert result == 0
    assert called["case_id"] == "demo_case"
    assert str(called["output_root"]).endswith("outputs")
    assert '"case_id": "demo_case"' in capsys.readouterr().out
