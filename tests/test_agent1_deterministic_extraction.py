from __future__ import annotations

from pathlib import Path

from signal_engine.agent1_extraction import (
    deduplicate_candidates,
    forbid_raw_transcript_output,
    generate_candidates_for_transcript,
    validate_candidate,
)


def _candidates(text: str) -> list[dict[str, object]]:
    return generate_candidates_for_transcript(case_id="case_1", source_file="/tmp/manual.txt", source_sha256="sha256:abc", text=text)


def test_guidance_revision_direction_and_prior_missing() -> None:
    rows = _candidates("CFO: We raised revenue guidance for FY2024 above our prior outlook.\nCFO: We expect margin guidance for FY2024.\n")
    guidance = [row for row in rows if row["signal_type"] == "guidance_revision"]
    assert {row["suggested_direction"] for row in guidance} >= {"raised", "prior_missing"}


def test_analyst_pressure_vs_unpaired_question() -> None:
    rows = _candidates("Question-and-Answer\nAnalyst: Why is revenue demand weak?\nCFO: Demand is improving.\nAnalyst: Why are margins pressured?\n")
    pressure = [row for row in rows if row["signal_type"] == "analyst_pressure"]
    assert len(pressure) == 2
    assert any(row["false_positive_bucket"] == "analyst_only_unpaired" for row in pressure)


def test_hedging_uncertainty_reassurance_and_boilerplate_suppression() -> None:
    rows = _candidates(
        "Operator: Safe harbor and non-GAAP statement.\n"
        "CFO: It is hard to predict demand and revenue this quarter.\n"
        "CEO: We are confident in revenue guidance for FY2024.\n"
        "CEO: We are very excited.\n"
    )
    assert any(row["signal_type"] == "management_hedging" for row in rows)
    assert any(row["signal_type"] == "uncertainty" for row in rows)
    assert any(row["signal_type"] == "reassurance" for row in rows)
    assert any(row["false_positive_bucket"] == "generic_optimism" for row in rows)
    assert all("evidence_text" not in row for row in rows)


def test_answer_shift_types() -> None:
    rows = _candidates("Question-and-Answer\nAnalyst: Why is revenue down?\nCFO: We are not prepared to quantify revenue today.\n")
    answer_shift = [row for row in rows if row["signal_type"] == "answer_shift"]
    assert answer_shift[0]["suggested_direction"] == "refusal_to_quantify"


def test_candidate_validation_requires_source_hash_and_provenance() -> None:
    row = _candidates("CFO: We raised revenue guidance for FY2024.\n")[0]
    assert not validate_candidate(row)
    row["source_sha256"] = "missing"
    row["provenance_hash"] = ""
    errors = validate_candidate(row)
    assert any("source_sha256" in error for error in errors)
    assert any("provenance_hash" in error for error in errors)


def test_raw_transcript_output_path_forbidden() -> None:
    assert forbid_raw_transcript_output(Path("reports/agent1/raw_transcript.txt"))


def test_dedupe_suppresses_duplicate_overlapping_rule_candidates() -> None:
    rows = _candidates("CFO: We raised revenue guidance for FY2024.\n")
    doubled = rows + rows
    assert len(deduplicate_candidates(doubled)) == len(rows)
