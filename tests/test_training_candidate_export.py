from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_training_candidates.py"


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_training_candidate_export_separates_buckets(tmp_path: Path) -> None:
    gold = tmp_path / "gold.jsonl"
    weak = tmp_path / "weak.jsonl"
    external = tmp_path / "external.jsonl"
    retrieval = tmp_path / "retrieval.json"
    event = tmp_path / "events.jsonl"
    out = tmp_path / "out.json"
    _write_jsonl(gold, [{"id": "g1", "label": "risk_friction"}])
    _write_jsonl(weak, [{"id": "w1", "label": "risk_friction", "gold_label": "bad"}])
    _write_jsonl(external, [{"id": "e1", "label": "positive", "gold_label": "bad"}])
    retrieval.write_text(json.dumps({"examples": [{"id": "r1", "text": "evidence"}]}), encoding="utf-8")
    _write_jsonl(event, [{"id": "ev1", "event_window": "0,+1"}])

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gold",
            str(gold),
            "--weak",
            str(weak),
            "--external",
            str(external),
            "--retrieval",
            str(retrieval),
            "--event-study",
            str(event),
            "--out",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["counts"] == {
        "human_reviewed_gold": 1,
        "weak_labels": 1,
        "external_benchmark_rows": 1,
        "retrieval_only_records": 1,
        "event_study_cases": 1,
    }
    assert payload["human_reviewed_gold"][0]["gold_eligible"] is True
    assert payload["weak_labels"][0]["gold_eligible"] is False
    assert "gold_label" not in payload["weak_labels"][0]
