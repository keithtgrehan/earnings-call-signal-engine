from __future__ import annotations

import csv
import json
from pathlib import Path

from signal_engine.acquisition.nyse100 import register_manual_local_transcripts


def _call_folder(root: Path) -> Path:
    folder = root / "JPM_JPMorgan_Chase_Co" / "2025-12-31_FY2025_Q4"
    (folder / "transcript").mkdir(parents=True)
    (folder / "provenance").mkdir()
    return folder


def test_manual_local_registration_writes_path_hash_only(tmp_path: Path) -> None:
    folder = _call_folder(tmp_path)
    transcript = folder / "transcript" / "manual.txt"
    transcript.write_text("Operator: local rights-cleared transcript\n", encoding="utf-8")
    (folder / "provenance" / "rights_decision.json").write_text(
        json.dumps({"rights_status": "manual_local_review_only", "eval_allowed": True, "commit_allowed": False, "training_allowed": False}),
        encoding="utf-8",
    )

    rows = register_manual_local_transcripts(tmp_path, out_path=tmp_path / "registry.csv")

    assert len(rows) == 1
    row = rows[0]
    assert row["local_path"] == str(transcript)
    assert row["sha256"].startswith("sha256:")
    assert row["commit_allowed"] == "false"
    assert row["training_allowed"] == "false"
    assert row["eval_allowed"] == "true"
    registry_text = (tmp_path / "registry.csv").read_text(encoding="utf-8")
    assert "Operator:" not in registry_text


def test_unknown_manual_local_rights_are_not_eval_allowed(tmp_path: Path) -> None:
    folder = _call_folder(tmp_path)
    (folder / "transcript" / "unknown.txt").write_text("Operator: unknown rights\n", encoding="utf-8")
    (folder / "provenance" / "rights_decision.json").write_text(json.dumps({"rights_status": "unknown_fail_closed"}), encoding="utf-8")

    rows = register_manual_local_transcripts(tmp_path, out_path=tmp_path / "registry.csv")

    assert rows[0]["rights_status"] == "unknown_fail_closed"
    assert rows[0]["eval_allowed"] == "false"
    assert list(csv.DictReader((tmp_path / "registry.csv").open(newline="", encoding="utf-8")))[0]["commit_allowed"] == "false"
