from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_case_pipeline as pipeline  # noqa: E402


def make_case(tmp_path: Path, case_id: str = "AAPL_2026_Q1") -> Path:
    case_dir = tmp_path / case_id
    raw_dir = case_dir / "raw"
    labels_dir = case_dir / "labels"
    raw_dir.mkdir(parents=True)
    labels_dir.mkdir()
    sentence = (
        "Management said we are committed to investing in the platform while analysts asked about margin pressure "
        "and demand durability. "
    )
    (raw_dir / "transcript.txt").write_text(sentence * 180, encoding="utf-8")
    (case_dir / "metadata.json").write_text(json.dumps({"case_id": case_id}), encoding="utf-8")
    (labels_dir / "weak_labels.jsonl").write_text(
        json.dumps(
            {
                "type": "commitment",
                "text_span": "Management said we are committed to investing in the platform.",
                "start_char": 0,
                "end_char": 62,
                "confidence": 0.7,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (labels_dir / "gold_labels.jsonl").write_text("", encoding="utf-8")
    return case_dir


def args(case_id: str, root: Path, **kwargs: object):
    item = SimpleNamespace(
        case=case_id,
        root=str(root),
        stage=None,
        all=False,
        selected_csv=None,
        target_per_case=5,
    )
    for key, value in kwargs.items():
        setattr(item, key, value)
    return item


def test_validate_writes_validation_and_manifest(tmp_path: Path) -> None:
    case_dir = make_case(tmp_path)
    statuses: dict[str, object] = {}
    result = pipeline.run_stage(args(case_dir.name, tmp_path), tmp_path, "validate", statuses)
    pipeline.run_stage(args(case_dir.name, tmp_path), tmp_path, "manifest", statuses)
    assert result["status"] == "pass"
    assert (case_dir / "outputs" / "validation.json").exists()
    manifest = list(csv.DictReader((tmp_path / "corpus_manifest.csv").open()))
    assert manifest[0]["case_id"] == case_dir.name
    assert manifest[0]["has_raw_transcript"] == "True"


def test_no_selected_csv_does_not_create_gold_labels(tmp_path: Path) -> None:
    case_dir = make_case(tmp_path)
    pipeline.build_packet(tmp_path, case_dir.name, 5)
    result = pipeline.apply_selected_for_case(tmp_path, case_dir.name, None)
    assert result["status"] == "skipped"
    assert (case_dir / "labels" / "gold_labels.jsonl").read_text(encoding="utf-8") == ""


def test_eval_skips_without_valid_gold(tmp_path: Path) -> None:
    case_dir = make_case(tmp_path)
    result = pipeline.evaluate_case(tmp_path, case_dir.name)
    assert result["status"] == "skipped"
    assert "Evaluation skipped" in (case_dir / "outputs" / "error_analysis.md").read_text(encoding="utf-8")


def test_gold_stage_requires_selected_csv_for_conversion(tmp_path: Path) -> None:
    case_dir = make_case(tmp_path)
    result = pipeline.apply_selected_for_case(tmp_path, case_dir.name, None)
    assert result["status"] == "skipped"
    statuses: dict[str, object] = {}
    with pytest.raises(SystemExit):
        pipeline.run_stage(args(case_dir.name, tmp_path, stage="gold"), tmp_path, "gold", statuses)


def test_invalid_label_type_rejected(tmp_path: Path) -> None:
    case_dir = make_case(tmp_path)
    pipeline.build_packet(tmp_path, case_dir.name, 5)
    selected = tmp_path / "selected.csv"
    selected.write_text(
        "case_id,candidate_id,type,confidence,notes\n"
        f"{case_dir.name},{case_dir.name}_CAND_01,bad_label,high,Nope\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        pipeline.apply_selected_for_case(tmp_path, case_dir.name, selected)
