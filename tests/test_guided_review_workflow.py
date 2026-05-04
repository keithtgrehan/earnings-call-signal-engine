from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from review_next_batch import load_review_state, review_rows, write_review_state  # noqa: E402
from report_evaluation_readiness import readiness_payload, report_readiness  # noqa: E402
from update_gold_from_review import update_gold  # noqa: E402
from validate_reviewed_batch import validate_rows  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    fields = fieldnames or list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_review_cli_state_writes_decisions_and_preserves_columns(tmp_path: Path) -> None:
    source = tmp_path / "next_review_batch.csv"
    output = tmp_path / "reviewed_next_batch.csv"
    write_csv(
        source,
        [
            {
                "candidate_id": "c1",
                "case_id": "case",
                "text": "Pricing remains a renewal risk.",
                "weak_label": "risk_friction",
                "confidence": "0.4",
                "selection_reason": "low_confidence",
            },
            {
                "candidate_id": "c2",
                "case_id": "case",
                "text": "We will send owners by Tuesday.",
                "weak_label": "risk_friction",
                "confidence": "0.2",
                "selection_reason": "low_confidence",
            },
        ],
    )

    rows, fieldnames = load_review_state(source, output)
    answers = iter(["a", "", "e", "2", "corrected label"])
    review_rows(rows, reviewer="tester", input_func=lambda _prompt: next(answers))
    write_review_state(output, rows, fieldnames, backup=False)

    reviewed = read_csv(output)
    assert reviewed[0]["review_decision"] == "accept"
    assert reviewed[0]["final_label"] == "risk_friction"
    assert reviewed[1]["review_decision"] == "edit_label"
    assert reviewed[1]["final_label"] == "opportunity_commitment"
    assert reviewed[1]["review_notes"] == "corrected label"
    assert "selection_reason" in reviewed[0]


def test_reviewed_batch_schema_adds_required_review_columns(tmp_path: Path) -> None:
    source = tmp_path / "next_review_batch.csv"
    output = tmp_path / "reviewed_next_batch.csv"
    write_csv(
        source,
        [
            {
                "candidate_id": "c1",
                "case_id": "case",
                "text": "Demand timing is uncertain.",
                "weak_label": "uncertainty_hedging",
                "confidence": "0.4",
                "priority_score": "5",
            }
        ],
    )

    rows, fieldnames = load_review_state(source, output)

    assert rows[0]["candidate_id"] == "c1"
    assert "priority_score" in fieldnames
    for column in ("review_decision", "final_label", "reviewer", "reviewed_at", "review_notes"):
        assert column in fieldnames
        assert rows[0][column] == ""


def test_review_cli_resumes_and_backs_up_existing_output(tmp_path: Path) -> None:
    source = tmp_path / "next_review_batch.csv"
    output = tmp_path / "reviewed_next_batch.csv"
    rows = [
        {"candidate_id": "c1", "case_id": "case", "text": "risk", "weak_label": "risk_friction", "confidence": "0.4"},
        {"candidate_id": "c2", "case_id": "case", "text": "admin", "weak_label": "neutral", "confidence": "0.4"},
    ]
    write_csv(source, rows)
    write_csv(
        output,
        [
            {
                **rows[0],
                "review_decision": "accept",
                "final_label": "risk_friction",
                "reviewer": "tester",
                "reviewed_at": "2026-01-01T00:00:00Z",
                "review_notes": "",
            },
            {**rows[1], "review_decision": "", "final_label": "", "reviewer": "", "reviewed_at": "", "review_notes": ""},
        ],
    )

    loaded, fieldnames = load_review_state(source, output)
    answers = iter(["r", "junk"])
    review_rows(loaded, reviewer="tester", input_func=lambda _prompt: next(answers))
    backup = write_review_state(output, loaded, fieldnames)

    reviewed = read_csv(output)
    assert reviewed[0]["review_decision"] == "accept"
    assert reviewed[1]["review_decision"] == "reject"
    assert backup is not None
    assert backup.exists()


def test_review_validation_allows_valid_reviewed_rows() -> None:
    result = validate_rows(
        [
            {"candidate_id": "c1", "review_decision": "accept", "final_label": "risk_friction"},
            {"candidate_id": "c2", "review_decision": "edit_label", "final_label": "neutral"},
            {"candidate_id": "c3", "review_decision": "reject", "final_label": ""},
            {"candidate_id": "c4", "review_decision": "unclear", "final_label": ""},
            {"candidate_id": "c5", "review_decision": "skip", "final_label": ""},
            {"candidate_id": "c6", "review_decision": "", "final_label": ""},
        ]
    )

    assert result.valid
    assert result.accepted_rows == 2
    assert result.accepted_gold_labels == 2
    assert result.skipped_rows == 1
    assert result.unreviewed_rows == 1


def test_review_validation_rejects_invalid_labels() -> None:
    result = validate_rows([{"candidate_id": "c1", "review_decision": "accept", "final_label": "made_up"}])

    assert not result.valid
    assert "invalid final_label" in result.errors[0]


def test_review_validation_detects_duplicate_candidate_conflict() -> None:
    result = validate_rows(
        [
            {"candidate_id": "dup", "review_decision": "accept", "final_label": "risk_friction"},
            {"candidate_id": "dup", "review_decision": "reject", "final_label": ""},
        ]
    )

    assert not result.valid
    assert "conflicting duplicate review decisions" in result.errors[0]


def test_update_gold_from_review_dry_run_does_not_train(tmp_path: Path) -> None:
    reviewed = tmp_path / "reviewed_next_batch.csv"
    write_csv(
        reviewed,
        [
            {
                "candidate_id": "c1",
                "case_id": "case",
                "text": "Pricing remains a renewal risk.",
                "weak_label": "risk_friction",
                "confidence": "0.4",
                "review_decision": "accept",
                "final_label": "risk_friction",
                "reviewer": "tester",
                "reviewed_at": "2026-01-01T00:00:00Z",
                "review_notes": "",
            }
        ],
    )

    summary = update_gold(reviewed, dry_run=True)

    assert summary["dry_run"] is True
    assert summary["accepted_gold_labels"] == 1
    assert summary["training_ran"] is False


def test_evaluation_readiness_detects_duplicate_gold_label_ids() -> None:
    payload = readiness_payload(
        gold_rows=[
            {"id": "dup", "text": "pricing risk", "signal_family": "risk_friction"},
            {"id": "dup", "text": "demand risk", "signal_family": "risk_friction"},
        ],
        reviewed_rows=[],
    )

    assert payload["duplicate_gold_ids"] == ["dup"]
    assert payload["benchmark_claims_allowed"] is False


def test_empty_evaluation_readiness_writes_coverage_without_metrics_claims(tmp_path: Path) -> None:
    gold = tmp_path / "gold_labels.jsonl"
    reviewed = tmp_path / "reviewed_next_batch.csv"
    coverage = tmp_path / "label_coverage.csv"
    report = tmp_path / "first_50_benchmark_report.md"
    readiness_json = tmp_path / "evaluation_readiness.json"
    gold.write_text("", encoding="utf-8")

    payload = report_readiness(
        gold_path=gold,
        reviewed_path=reviewed,
        coverage_out=coverage,
        report_out=report,
        json_out=readiness_json,
    )

    assert payload["gold_labels"] == 0
    assert payload["metrics_allowed"] is False
    assert payload["benchmark_claims_allowed"] is False
    coverage_rows = read_csv(coverage)
    assert {row["label"] for row in coverage_rows} == {
        "neutral",
        "opportunity_commitment",
        "risk_friction",
        "uncertainty_hedging",
    }
    assert all(row["gold_count"] == "0" for row in coverage_rows)
    assert "must not claim precision, recall, F1" in report.read_text(encoding="utf-8")
