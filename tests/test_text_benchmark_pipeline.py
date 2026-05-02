from __future__ import annotations

import csv
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from build_gold_labels import build_gold  # noqa: E402
from build_review_queue import build_review_queue  # noqa: E402
from evaluate_gold_labels import evaluate, gate_for_count  # noqa: E402
from labeling_common import parse_packet  # noqa: E402
from train_text_signal_model import train, training_gate  # noqa: E402


def test_parse_packet_preserves_duplicates_and_noise_flags(tmp_path: Path) -> None:
    packet = tmp_path / "packet.csv"
    packet.write_text(
        "id,case_id,text,suggested_label,suggestion_confidence,reason\n"
        "a,case1,This pricing risk is unresolved,risk_friction,high,pricing\n"
        "b,case1,This pricing risk is unresolved,risk_friction,high,duplicate\n"
        "c,case2,Forward-looking statements may differ from actual results,neutral,low,disclaimer\n",
        encoding="utf-8",
    )

    rows = parse_packet(packet)

    assert len(rows) == 3
    assert rows[1]["duplicate_of"] == "a"
    assert "disclaimer" in rows[2]["noise_flag"]
    assert rows[0]["text"] == "This pricing risk is unresolved"


def test_parse_packet_reads_safe_zip_without_extracting(tmp_path: Path) -> None:
    packet = tmp_path / "packet.zip"
    with zipfile.ZipFile(packet, "w") as archive:
        archive.writestr("nested/candidates.jsonl", '{"id":"z1","text":"We commit to the pilot","suggested_label":"opportunity_commitment"}\n')

    rows = parse_packet(packet)

    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "z1"
    assert rows[0]["weak_label"] == "opportunity_commitment"


def test_review_queue_does_not_filter_rows_and_prioritizes_low_confidence() -> None:
    candidates = [
        {"candidate_id": "a", "case_id": "c1", "text": "plain update", "weak_label": "neutral", "confidence": 0.9, "noise_flag": ""},
        {"candidate_id": "b", "case_id": "c1", "text": "pricing risk unresolved", "weak_label": "risk_friction", "confidence": 0.2, "noise_flag": ""},
    ]

    queue = build_review_queue(candidates)

    assert len(queue) == 2
    assert queue[0]["candidate_id"] == "b"
    assert "low_confidence" in str(queue[0]["priority_reason"])


def test_gold_builder_accepts_only_accepted_rows() -> None:
    rows = [
        {"candidate_id": "a", "case_id": "c1", "text": "risk", "weak_label": "risk_friction", "final_label": "risk_friction", "review_decision": "accept"},
        {"candidate_id": "b", "case_id": "c1", "text": "risk", "weak_label": "risk_friction", "final_label": "risk_friction", "review_decision": "reject"},
        {"candidate_id": "c", "case_id": "c1", "text": "risk", "weak_label": "risk_friction", "final_label": "risk_friction", "review_decision": "unclear"},
    ]

    accepted, rejected, unclear = build_gold(rows)

    assert [row["candidate_id"] for row in accepted] == ["a"]
    assert len(rejected) == 1
    assert len(unclear) == 1


def test_evaluation_gate_thresholds_and_training_guard(tmp_path: Path) -> None:
    assert gate_for_count(19) == ("insufficient_data", False)
    assert gate_for_count(20) == ("preliminary_metrics_only", True)
    assert gate_for_count(100) == ("early_benchmark", True)
    assert gate_for_count(500) == ("train_dev_test_split_allowed", True)
    assert training_gate(49) == "skip_training"
    assert training_gate(50) == "weak_baseline_allowed"
    assert training_gate(201) == "full_baseline_allowed"

    payload = evaluate([])
    assert payload["metrics_computed"] is False

    summary, errors = train([], model_out=tmp_path / "latest.joblib")
    assert summary["training_ran"] is False
    assert errors == []
    assert not (tmp_path / "latest.joblib").exists()


def test_reviewed_label_csv_roundtrip_shape(tmp_path: Path) -> None:
    path = tmp_path / "reviewed.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "case_id", "text", "weak_label", "confidence", "noise_flag", "review_decision", "final_label"])
        writer.writeheader()
        writer.writerow(
            {
                "candidate_id": "a",
                "case_id": "case",
                "text": "We will commit next week",
                "weak_label": "opportunity_commitment",
                "confidence": "0.8",
                "noise_flag": "",
                "review_decision": "accept",
                "final_label": "opportunity_commitment",
            }
        )
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    accepted, _, _ = build_gold(rows)
    assert accepted[0]["signal_family"] == "opportunity_commitment"
