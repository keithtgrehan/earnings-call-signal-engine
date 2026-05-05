from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from normalize_and_import_labels import import_sources  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_import_sources_normalizes_guidance_and_dedupes(tmp_path: Path) -> None:
    human_labels = tmp_path / "human_reviewed_signal_labels.jsonl"
    human_labels.write_text(
        json.dumps(
            {
                "id": "human_001",
                "case_id": "call_alpha",
                "text": "The customer may expand after the pilot.",
                "signal_family": "opportunity_commitment",
                "notes": "Existing human-reviewed label.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    guidance_labels = tmp_path / "labels.csv"
    write_csv(
        guidance_labels,
        [
            {
                "call_id": "call_beta",
                "guidance_change_label": "lowered",
                "evidence_text": "We lowered full-year guidance.",
                "ticker": "XYZ",
                "company": "Example Co",
                "quarter": "Q1_2026",
                "confidence": "0.8",
                "notes": "Explicit guidance change.",
            }
        ],
    )
    gold = tmp_path / "gold_labels.jsonl"
    summary = tmp_path / "summary.md"

    first = import_sources([human_labels, guidance_labels], gold, summary)
    second = import_sources([human_labels, guidance_labels], gold, summary)
    rows = read_jsonl(gold)

    assert first["gold_total"] == 2
    assert len(first["imported"]) == 2
    assert second["gold_total"] == 2
    assert len(second["imported"]) == 0
    assert {row["signal_family"] for row in rows} == {"opportunity_commitment", "risk_friction"}
    guidance_row = next(row for row in rows if row["case_id"] == "call_beta")
    assert guidance_row["metadata"]["label_mapping"] == "guidance_change_label:lowered"
    assert guidance_row["metadata"]["original_label"] == "lowered"
    assert "duplicate id or case/text/label" in summary.read_text(encoding="utf-8")


def test_import_sources_rejects_unreviewed_review_csv(tmp_path: Path) -> None:
    reviewed = tmp_path / "reviewed_labels.csv"
    write_csv(
        reviewed,
        [
            {
                "candidate_id": "cand_001",
                "case_id": "call_alpha",
                "text": "This row was never accepted.",
                "final_label": "",
                "review_decision": "",
            }
        ],
    )
    gold = tmp_path / "gold_labels.jsonl"
    summary = tmp_path / "summary.md"

    result = import_sources([reviewed], gold, summary)

    assert result["gold_total"] == 0
    assert len(result["imported"]) == 0
    assert result["sources"][0]["schema"] == "reviewed_csv"
    assert result["sources"][0]["rows_rejected"] == 1
    assert not gold.exists()
