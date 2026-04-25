from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LABEL_BUILD_SCRIPT = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
PILOT_BUILD_SCRIPT = ROOT / "scripts" / "build_multimodal_pilot_cases.py"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_build_multimodal_pilot_cases_outputs_seed_cases(tmp_path: Path) -> None:
    labels_path = ROOT / "data" / "nlp_research" / "human_reviewed_signal_labels.jsonl"
    if not labels_path.exists():
        subprocess.run(
            [sys.executable, str(LABEL_BUILD_SCRIPT)],
            cwd=ROOT,
            check=True,
        )

    out_path = tmp_path / "multimodal_pilot_cases.jsonl"
    subprocess.run(
        [
            sys.executable,
            str(PILOT_BUILD_SCRIPT),
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = _load_jsonl(out_path)
    assert 8 <= len(rows) <= 12
    assert all(row["audio_file"] is None for row in rows)
    assert all(row["video_file"] is None for row in rows)
    assert {
        "id",
        "domain",
        "transcript_text",
        "expected_signal_family",
        "expected_review_action",
        "audio_file",
        "video_file",
        "transcript_evidence",
        "audio_expected_cues",
        "video_expected_cues",
        "status",
        "limitations",
    } <= set(rows[0])

