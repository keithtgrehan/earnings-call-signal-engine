from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "transcript_downloader"
SRC = ROOT / "src"
for path in (str(TOOLS), str(SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

import apply_selected_candidates_batch as batch  # noqa: E402
import audit_selected_candidates as audit  # noqa: E402
from apply_selected_gold_labels import build_labels_for_case, load_selected, write_labels_for_case  # noqa: E402
from run_corpus_analysis import evaluate_case_labels  # noqa: E402
from signal_engine.pipeline import analyze_conversation_record  # noqa: E402


def make_case(tmp_path: Path, case_id: str = "AAPL_2026_Q1") -> tuple[Path, str]:
    case_dir = tmp_path / case_id
    raw_dir = case_dir / "raw"
    labels_dir = case_dir / "labels"
    raw_dir.mkdir(parents=True)
    labels_dir.mkdir()
    quote = "Analysts asked whether demand durability and margin pressure could reverse next quarter."
    raw_text = (
        "Operator: Welcome to the call.\n"
        f"{quote}\n"
        "Management: We will continue investing in the platform.\n"
    )
    (raw_dir / "transcript.txt").write_text(raw_text, encoding="utf-8")
    (labels_dir / "human_labeling_packet.md").write_text(
        "\n".join(
            [
                f"# Human Labeling Packet: {case_id}",
                "",
                "## CAND-01",
                "",
                f"- candidate_id: `{case_id}_CAND_01`",
                "- suggested_label: `analyst_pressure`",
                "- suggested_confidence: `medium`",
                "- source_file: `weak_labels.jsonl`",
                "",
                "```text",
                quote,
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    start = raw_text.index(quote)
    end = start + len(quote)
    (labels_dir / "weak_labels.jsonl").write_text(
        json.dumps(
            {
                "type": "analyst_pressure",
                "text_span": quote,
                "start_char": start,
                "end_char": end,
                "confidence": 0.75,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return case_dir, quote


def write_selected(path: Path, case_id: str, label_type: str = "analyst_pressure") -> None:
    path.write_text(
        "case_id,candidate_id,type,confidence,notes\n"
        f"{case_id},{case_id}_CAND_01,{label_type},high,Approved test row\n",
        encoding="utf-8",
    )


def test_selected_csv_audit_flags_schema_and_duplicates(tmp_path: Path) -> None:
    case_dir, _ = make_case(tmp_path)
    rows = [
        {
            "case_id": case_dir.name,
            "candidate_id": f"{case_dir.name}_CAND_01",
            "type": "analyst_pressure",
            "confidence": "high",
            "notes": "One",
        },
        {
            "case_id": case_dir.name,
            "candidate_id": f"{case_dir.name}_CAND_01",
            "type": "bad_type",
            "confidence": "certain",
            "notes": "",
        },
    ]
    audited, summary = audit.audit_rows(rows, root=tmp_path)
    assert summary["row_count"] == 2
    assert audited[1]["duplicate_candidate_id"] is True
    assert "invalid_type" in audited[1]["warnings"]
    assert "invalid_confidence" in audited[1]["warnings"]
    assert "missing_notes" in audited[1]["warnings"]


def test_draft_and_human_approved_writing_are_separate(tmp_path: Path) -> None:
    case_dir, _ = make_case(tmp_path)
    selected = tmp_path / "selected.csv"
    write_selected(selected, case_dir.name)
    rows = load_selected(selected)

    draft_labels = build_labels_for_case(tmp_path, case_dir.name, rows, label_status="draft_reviewed")
    draft_out = write_labels_for_case(case_dir, draft_labels, label_status="draft_reviewed")
    assert draft_out.name == "draft_gold_labels.jsonl"
    assert json.loads(draft_out.read_text(encoding="utf-8").splitlines()[0])["human_label"] is False

    human_labels = build_labels_for_case(tmp_path, case_dir.name, rows, label_status="human_approved")
    gold_out = write_labels_for_case(case_dir, human_labels, label_status="human_approved")
    assert gold_out.name == "gold_labels.jsonl"
    assert json.loads(gold_out.read_text(encoding="utf-8").splitlines()[0])["human_label"] is True


def test_human_approved_gold_is_not_overwritten_without_flag(tmp_path: Path) -> None:
    case_dir, _ = make_case(tmp_path)
    selected = tmp_path / "selected.csv"
    write_selected(selected, case_dir.name)
    rows = load_selected(selected)
    labels = build_labels_for_case(tmp_path, case_dir.name, rows, label_status="human_approved")
    write_labels_for_case(case_dir, labels, label_status="human_approved")

    with pytest.raises(SystemExit):
        write_labels_for_case(case_dir, labels, label_status="human_approved")


def test_batch_conversion_reports_unknown_candidate_failure(tmp_path: Path) -> None:
    make_case(tmp_path)
    rows = [
        {
            "case_id": "AAPL_2026_Q1",
            "candidate_id": "AAPL_2026_Q1_CAND_99",
            "type": "analyst_pressure",
            "confidence": "high",
            "notes": "Unknown candidate",
        }
    ]
    report_rows = batch.apply_batch(
        root=tmp_path,
        selected_rows=rows,
        out_dir=tmp_path,
        label_status="draft_reviewed",
    )
    report = tmp_path / "selected_candidates_batch_report.csv"
    assert report.exists()
    csv_rows = list(csv.DictReader(report.open(encoding="utf-8")))
    assert report_rows[0]["status"] == "failed"
    assert csv_rows[0]["status"] == "failed"


def test_final_evaluation_ignores_draft_labels(tmp_path: Path) -> None:
    case_dir, _ = make_case(tmp_path)
    selected = tmp_path / "selected.csv"
    write_selected(selected, case_dir.name)
    rows = load_selected(selected)
    draft_labels = build_labels_for_case(tmp_path, case_dir.name, rows, label_status="draft_reviewed")
    write_labels_for_case(case_dir, draft_labels, label_status="draft_reviewed")

    final_row, _ = evaluate_case_labels(case_dir)
    draft_row, _ = evaluate_case_labels(
        case_dir,
        label_filename="draft_gold_labels.jsonl",
        require_human_label=False,
        label_count_field="draft_label_count",
    )

    assert final_row is None
    assert draft_row is not None
    assert draft_row["draft_label_count"] == 1


def test_domain_adapter_schema_accepts_renewals_and_hr() -> None:
    renewal_result = analyze_conversation_record(
        {
            "conversation_id": "renewal_case",
            "messages": [
                {"role": "customer", "text": "We are not renewing unless the unresolved issue is fixed."},
                {"role": "csm", "text": "I own the recovery plan and will follow up tomorrow."},
            ],
        },
        domain="renewals",
    )
    hr_result = analyze_conversation_record(
        {
            "conversation_id": "hr_case",
            "messages": [
                {"role": "employee", "text": "The team is burned out and worried about the promotion policy."},
                {"role": "hrbp", "text": "I will check the policy and share next steps."},
            ],
        },
        domain="hr",
    )

    assert renewal_result["domain"] == "renewals"
    assert any(flag.startswith("account_") for flag in renewal_result["risk_flags"] + renewal_result["opportunity_flags"])
    assert hr_result["domain"] == "hr"
    assert "hr_engagement_risk" in hr_result["risk_flags"]
