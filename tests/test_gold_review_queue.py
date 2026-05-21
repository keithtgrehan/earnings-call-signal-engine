from __future__ import annotations

import csv
import json
from pathlib import Path

from signal_engine.review_queue.build import build_queue
from signal_engine.review_queue.context import TranscriptIndex
from signal_engine.review_queue.parsers import parse_files
from signal_engine.review_queue.priority import priority_for
from signal_engine.review_queue.schema import HUMAN_ADJUDICATION_FIELDS, validate_row
from signal_engine.review_queue.writers import write_outputs


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_normal_packet_parsing(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "human_labeling_packet.md",
        """# Human Labeling Packet: TEST_2026_Q1

## CAND-01

- candidate_id: `TEST_2026_Q1_CAND_01`
- suggested_label: `risk_friction`
- suggested_confidence: `0.82`
- reason: analyst_pressure + guidance_revision
- source_file: `data/corpus/high_signal_cases/TEST_2026_Q1/raw/transcript.txt`

```text
Analyst pressure increased after management lowered revenue guidance by 5%.
```
""",
    )

    rows = parse_files([packet])

    assert rows[0]["case_id"] == "TEST_2026_Q1"
    assert rows[0]["candidate_id"] == "TEST_2026_Q1_CAND_01"
    assert rows[0]["suggested_label"] == "risk_friction"
    assert "lowered revenue guidance" in rows[0]["evidence_span"]
    assert rows[0]["parser_warning"] == ""


def test_combined_packet_parsing_with_case_dividers(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "combined.md",
        """==============================
CASE: COMBO_2026_Q2
SOURCE: /tmp/combo/human_labeling_packet.md
==============================

## CAND-02

- suggested_label: `uncertainty_hedging`
- suggested_confidence: `medium`
- reason: guidance_revision
- source_file: `combo.txt`

```text
We expect a wider range of outcomes next fiscal year.
```
""",
    )

    rows = parse_files([packet])

    assert rows[0]["case_id"] == "COMBO_2026_Q2"
    assert rows[0]["candidate_id"] == "COMBO_2026_Q2_CAND_02"
    assert rows[0]["source_file"] == "combo.txt"


def test_existing_repo_packet_style_parsing(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "human_labeling_packet.md",
        """# Human Labeling Packet: MSFT_2025_Q2

### MSFT_2025_Q2_weak_0001

- suggested_label: `uncertainty_hedging`
- confidence: `0.75`
- evidence_terms: `guidance outlook`

> Management said outlook commentary will include a wider range than usual.
""",
    )

    rows = parse_files([packet])

    assert rows[0]["candidate_id"] == "MSFT_2025_Q2_weak_0001"
    assert rows[0]["suggested_confidence"] == "0.75"
    assert rows[0]["reason"] == "guidance outlook"
    assert "Management said outlook" in rows[0]["evidence_span"]


def test_malformed_candidate_and_missing_evidence_are_retained(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "bad.md",
        """# Human Labeling Packet: BAD_2026_Q1

## CAND-01

- candidate_id: `BAD_2026_Q1_CAND_01`
- suggested_label: `neutral`
""",
    )

    rows = parse_files([packet])

    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "BAD_2026_Q1_CAND_01"
    assert "missing_evidence_span" in rows[0]["parser_warning"]
    assert "missing_reason" in rows[0]["parser_warning"]


def test_duplicate_candidate_id_preserves_duplicate_count(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "dupes.md",
        """# Human Labeling Packet: DUP_2026_Q1

## CAND-01
- candidate_id: `DUP_2026_Q1_CAND_01`
- suggested_label: `neutral`
- suggested_confidence: `low`
- reason: keyword
```text
First span.
```

## CAND-02
- candidate_id: `DUP_2026_Q1_CAND_01`
- suggested_label: `neutral`
- suggested_confidence: `low`
- reason: keyword
```text
Second span.
```
""",
    )

    rows = parse_files([packet])

    assert len(rows) == 1
    assert rows[0]["duplicate_count"] == "2"


def test_weak_label_jsonl_parsing(tmp_path: Path) -> None:
    weak = write(
        tmp_path / "weak_label_candidates.jsonl",
        json.dumps(
            {
                "candidate_id": "WEAK_2026_Q1_weak_0001",
                "case_id": "WEAK_2026_Q1",
                "text": "Demand is uncertain and revenue guidance may move lower.",
                "predicted_label": "uncertainty_hedging",
                "confidence": 0.77,
                "evidence_terms": ["demand", "guidance"],
            }
        )
        + "\n",
    )

    rows = parse_files([weak])

    assert rows[0]["source_type"] == "weak_label_jsonl"
    assert rows[0]["suggested_label"] == "uncertainty_hedging"
    assert rows[0]["reason"] == "demand; guidance"


def test_exact_transcript_context_match(tmp_path: Path) -> None:
    transcript = write(tmp_path / "CTX_2026_Q1" / "raw" / "transcript.txt", "Before sentence. Exact evidence span appears here. After sentence.")
    index = TranscriptIndex([transcript])

    match = index.match("CTX_2026_Q1", "Exact evidence span appears here.", context_chars=500, context_sentences=1)

    assert match.evidence_match_status == "exact_match"
    assert "Before sentence" in match.context_before
    assert "After sentence" in match.context_after


def test_normalized_whitespace_transcript_context_match(tmp_path: Path) -> None:
    transcript = write(tmp_path / "NORM_2026_Q1" / "raw" / "transcript.txt", "Before. Revenue guidance\n\nwill expand   next year. After.")
    index = TranscriptIndex([transcript])

    match = index.match("NORM_2026_Q1", "Revenue guidance will expand next year.", context_chars=500, context_sentences=1)

    assert match.evidence_match_status == "normalized_whitespace_match"
    assert match.transcript_file_if_matched


def test_no_transcript_context_match(tmp_path: Path) -> None:
    transcript = write(tmp_path / "MISS_2026_Q1" / "raw" / "transcript.txt", "Completely unrelated transcript.")
    index = TranscriptIndex([transcript])

    match = index.match("MISS_2026_Q1", "Evidence that is absent.", context_chars=500, context_sentences=1)

    assert match.evidence_match_status == "unmatched_context"
    assert match.context_before == ""
    assert match.context_after == ""


def test_priority_high_for_analyst_pressure_guidance_revision() -> None:
    priority, reason, boilerplate = priority_for(
        {
            "suggested_label": "uncertainty_hedging",
            "reason": "analyst_pressure + guidance_revision",
            "evidence_span": "The analyst pressed management after revenue guidance declined by 8%.",
        }
    )

    assert priority == "HIGH"
    assert reason.startswith("high_reason")
    assert boilerplate is False


def test_priority_low_for_boilerplate_disclaimer() -> None:
    priority, reason, boilerplate = priority_for(
        {
            "suggested_label": "risk_friction",
            "reason": "keyword",
            "evidence_span": "This call is being recorded and contains forward-looking statements subject to risks and uncertainties.",
        }
    )

    assert priority == "LOW"
    assert reason == "low_boilerplate_or_disclaimer_text"
    assert boilerplate is True


def test_csv_and_jsonl_output_creation(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "OUT_2026_Q1" / "labels" / "human_labeling_packet.md",
        """# Human Labeling Packet: OUT_2026_Q1

## CAND-01
- candidate_id: `OUT_2026_Q1_CAND_01`
- suggested_label: `risk_friction`
- suggested_confidence: `0.9`
- reason: guidance_revision
- source_file: `OUT_2026_Q1/raw/transcript.txt`
```text
Revenue guidance declined by 5% for fiscal 2026.
```
""",
    )
    transcript = write(
        tmp_path / "OUT_2026_Q1" / "raw" / "transcript.txt",
        "Intro. Revenue guidance declined by 5% for fiscal 2026. Closing.",
    )
    out_dir = tmp_path / "gold_review"
    rows, issues, _metadata = build_queue(
        packet_values=[str(packet)],
        transcript_values=[str(transcript)],
        verbose=False,
    )

    write_outputs(out_dir, rows, issues, include_csv=True, include_jsonl=True)

    assert (out_dir / "review_queue.csv").exists()
    assert (out_dir / "review_queue.jsonl").exists()
    assert (out_dir / "summary_by_case_label.csv").exists()
    assert (out_dir / "summary_by_priority.csv").exists()
    assert (out_dir / "prompt_pack" / "deep_research_prompt.md").exists()
    with (out_dir / "review_queue.csv").open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert csv_rows[0]["human_decision"] == ""
    assert csv_rows[0]["evidence_match_status"] == "exact_match"


def test_queue_builder_never_writes_gold_labels(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "SAFE_2026_Q1" / "labels" / "human_labeling_packet.md",
        """# Human Labeling Packet: SAFE_2026_Q1

## CAND-01
- candidate_id: `SAFE_2026_Q1_CAND_01`
- suggested_label: `risk_friction`
- suggested_confidence: `0.9`
- reason: guidance_revision
- source_file: `SAFE_2026_Q1/raw/transcript.txt`
```text
Revenue guidance declined by 5% for fiscal 2026.
```
""",
    )
    out_dir = tmp_path / "artifacts" / "gold_review"
    gold_dir = tmp_path / "data" / "gold"

    rows, issues, _metadata = build_queue(packet_values=[str(packet)], transcript_values=[], verbose=False)
    write_outputs(out_dir, rows, issues, include_csv=True, include_jsonl=True)

    assert not gold_dir.exists()
    assert not list(tmp_path.rglob("gold_labels*.jsonl"))
    assert not list(tmp_path.rglob("*confirmed*"))
    assert not list(tmp_path.rglob("*promoted*"))


def test_human_fields_remain_blank_on_generated_queue(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "BLANK_2026_Q1" / "labels" / "human_labeling_packet.md",
        """# Human Labeling Packet: BLANK_2026_Q1

## CAND-01
- candidate_id: `BLANK_2026_Q1_CAND_01`
- suggested_label: `uncertainty_hedging`
- suggested_confidence: `0.8`
- reason: guidance outlook
- source_file: `BLANK_2026_Q1/raw/transcript.txt`
```text
Management said the outlook range could widen next quarter.
```
""",
    )

    rows, _issues, _metadata = build_queue(packet_values=[str(packet)], transcript_values=[], verbose=False)

    assert rows
    for field in HUMAN_ADJUDICATION_FIELDS:
        assert rows[0][field] == ""


def test_missing_evidence_fails_validation() -> None:
    issues = validate_row(
        {
            "case_id": "MISS_2026_Q1",
            "candidate_id": "MISS_2026_Q1_CAND_01",
            "suggested_label": "risk_friction",
            "suggested_confidence": "0.8",
            "reason": "guidance_revision",
            "source_file": "MISS_2026_Q1/raw/transcript.txt",
            "packet_file": "MISS_2026_Q1/labels/human_labeling_packet.md",
            "evidence_span": "",
        }
    )

    assert any(issue.field == "evidence_span" for issue in issues)


def test_missing_provenance_fails_validation() -> None:
    issues = validate_row(
        {
            "case_id": "MISS_2026_Q1",
            "candidate_id": "MISS_2026_Q1_CAND_01",
            "suggested_label": "risk_friction",
            "suggested_confidence": "0.8",
            "reason": "guidance_revision",
            "source_file": "",
            "packet_file": "",
            "evidence_span": "Revenue guidance declined by 5%.",
        }
    )

    issue_fields = {issue.field for issue in issues}
    assert {"source_file", "packet_file"} <= issue_fields


def test_candidate_gold_separation_is_preserved(tmp_path: Path) -> None:
    packet = write(
        tmp_path / "CAND_2026_Q1" / "labels" / "human_labeling_packet.md",
        """# Human Labeling Packet: CAND_2026_Q1

## CAND-01
- candidate_id: `CAND_2026_Q1_CAND_01`
- suggested_label: `opportunity_commitment`
- suggested_confidence: `0.9`
- reason: guidance_revision
- source_file: `CAND_2026_Q1/raw/transcript.txt`
```text
Management raised its revenue outlook and committed to higher investment.
```
""",
    )

    rows, issues, _metadata = build_queue(packet_values=[str(packet)], transcript_values=[], verbose=False)

    assert issues == []
    assert rows[0]["candidate_id"] == "CAND_2026_Q1_CAND_01"
    assert rows[0]["human_decision"] == ""
    assert rows[0]["final_label"] == ""
    assert rows[0]["final_evidence_span"] == ""
    assert rows[0]["normalized_label"] == "opportunity_commitment"
