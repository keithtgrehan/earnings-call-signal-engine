from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from priority_review_common import LABELS, PACKET_CSV, REVIEW_FIELDS, read_jsonl  # noqa: E402
from promote_priority_review import promote  # noqa: E402


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_priority_review_packet_generation_preserves_gold() -> None:
    gold_path = ROOT / "data" / "gold" / "gold_labels.jsonl"
    before = gold_path.read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "prepare_priority_review.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "packet_rows" in result.stdout
    assert gold_path.read_text(encoding="utf-8") == before
    rows = read_csv_rows(PACKET_CSV)
    assert rows
    assert set(REVIEW_FIELDS).issubset(rows[0])
    assert {row["predicted_label"] for row in rows}.issubset(set(LABELS))
    assert (ROOT / "reports" / "call_review_inventory.md").exists()
    assert (ROOT / "reports" / "transcript_download_plan.md").exists()


def test_promotion_imports_only_accepted_and_dedupes(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.csv"
    gold_path = tmp_path / "gold.jsonl"
    existing = {
        "id": "existing",
        "case_id": "NVDA_2026_Q4_call07",
        "text": "duplicate span",
        "signal_family": "risk_friction",
    }
    gold_path.write_text(json.dumps(existing) + "\n", encoding="utf-8")
    rows = [
        {
            "review_id": "r1",
            "case_id": "NVDA_2026_Q4_call07",
            "ticker": "NVDA",
            "fiscal_period": "Q4_2026",
            "source_path": "data/corpus/processed/evidence_objects/NVDA_2026_Q4_call07.evidence_objects.jsonl",
            "section": "question_and_answer",
            "speaker": "analyst",
            "evidence_text": "Clear accepted span with guidance risk pressure.",
            "predicted_label": "risk_friction",
            "alternative_label_if_ambiguous": "",
            "trigger_terms": "risk",
            "deterministic_confidence": "0.8",
            "ml_prediction_if_available": "risk_friction",
            "disagreement_flag": "no",
            "review_priority_reason": "test",
            "reviewer_decision": "accept",
            "corrected_label": "",
            "reviewer_notes": "good",
        },
        {
            "review_id": "r2",
            "case_id": "NVDA_2026_Q4_call07",
            "ticker": "NVDA",
            "fiscal_period": "Q4_2026",
            "source_path": "x",
            "section": "",
            "speaker": "",
            "evidence_text": "duplicate span",
            "predicted_label": "risk_friction",
            "alternative_label_if_ambiguous": "",
            "trigger_terms": "",
            "deterministic_confidence": "",
            "ml_prediction_if_available": "",
            "disagreement_flag": "",
            "review_priority_reason": "",
            "reviewer_decision": "accept",
            "corrected_label": "",
            "reviewer_notes": "",
        },
        {
            "review_id": "r3",
            "case_id": "NVDA_2026_Q4_call07",
            "ticker": "NVDA",
            "fiscal_period": "Q4_2026",
            "source_path": "x",
            "section": "",
            "speaker": "",
            "evidence_text": "Rejected span",
            "predicted_label": "neutral",
            "alternative_label_if_ambiguous": "",
            "trigger_terms": "",
            "deterministic_confidence": "",
            "ml_prediction_if_available": "",
            "disagreement_flag": "",
            "review_priority_reason": "",
            "reviewer_decision": "reject",
            "corrected_label": "",
            "reviewer_notes": "",
        },
        {
            "review_id": "r4",
            "case_id": "NVDA_2026_Q4_call07",
            "ticker": "NVDA",
            "fiscal_period": "Q4_2026",
            "source_path": "x",
            "section": "",
            "speaker": "",
            "evidence_text": "Unclear span",
            "predicted_label": "neutral",
            "alternative_label_if_ambiguous": "",
            "trigger_terms": "",
            "deterministic_confidence": "",
            "ml_prediction_if_available": "",
            "disagreement_flag": "",
            "review_priority_reason": "",
            "reviewer_decision": "unclear",
            "corrected_label": "",
            "reviewer_notes": "",
        },
    ]
    with packet_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    payload = promote(packet_path, gold_path, dry_run=False, reviewer="Keith", report_path=tmp_path / "growth.md")
    assert payload["accepted_imported_count"] == 1
    assert payload["duplicate_skipped_count"] == 1
    gold_rows = read_jsonl(gold_path)
    assert len(gold_rows) == 2
    imported = gold_rows[-1]
    assert imported["label_source"] == "human_reviewed_priority_packet"
    assert imported["provenance_quality"] == "high"
    assert imported["requires_manual_review"] is False


def test_eval_after_review_make_target_exists() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "review-priority-labels:" in makefile
    assert "promote-reviewed-priority-labels:" in makefile
    assert "eval-after-review:" in makefile
    assert "tools/report_priority_review_validation.py" in makefile
