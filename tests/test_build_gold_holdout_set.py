from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
HOLDOUT_SCRIPT = ROOT / "scripts" / "build_gold_holdout_set.py"


def test_build_gold_holdout_set_creates_balanced_candidates(tmp_path: Path) -> None:
    labels_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    holdout_path = tmp_path / "gold_holdout_candidates.jsonl"

    subprocess.run([sys.executable, str(BUILD_SCRIPT), "--out", str(labels_path)], cwd=ROOT, check=True)
    subprocess.run(
        [
            sys.executable,
            str(HOLDOUT_SCRIPT),
            "--input-path",
            str(labels_path),
            "--out",
            str(holdout_path),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = [json.loads(line) for line in holdout_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = Counter(row["signal_family"] for row in rows)

    assert 12 <= len(rows) <= 20
    assert set(counts.values()) == {4}
    assert all(row["locked_for_training"] is True for row in rows)
    assert all(row["gold_status"] == "candidate_pending_second_review" for row in rows)
