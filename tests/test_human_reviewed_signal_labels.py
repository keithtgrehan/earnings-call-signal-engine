from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"


def _load_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_build_human_reviewed_signal_labels_outputs_expected_shape(tmp_path: Path) -> None:
    out_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = _load_rows(out_path)
    counts = Counter(row["signal_family"] for row in rows)

    assert len(rows) >= 40
    assert {"risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral"} == set(counts)
    assert counts["risk_friction"] >= 10
    assert counts["opportunity_commitment"] >= 10
    assert counts["uncertainty_hedging"] >= 10
    assert counts["neutral"] >= 10

    first = rows[0]
    assert {
        "id",
        "source_file",
        "domain",
        "text",
        "signal_family",
        "label_source",
        "evidence_terms",
        "rationale",
        "pii_redacted",
        "notes",
    } <= set(first)
    assert all(row["label_source"] == "human_seeded_v1" for row in rows)


def test_human_reviewed_signal_labels_do_not_store_raw_email_or_phone(tmp_path: Path) -> None:
    out_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = _load_rows(out_path)
    combined_text = "\n".join(row["text"] for row in rows)
    assert "@northwind.example" not in combined_text
    assert "+1 415 555" not in combined_text
    assert not re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", combined_text, re.IGNORECASE)
