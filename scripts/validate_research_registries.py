#!/usr/bin/env python3
"""Validate rights-safe research registry CSVs for training readiness."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


SOURCE_REGISTRY_PATH = "data/research/llm_quant_source_registry.csv"
FEATURE_BACKLOG_PATH = "data/research/future_feature_backlog.csv"
DATASET_TARGETS_PATH = "data/research/future_dataset_targets.csv"

SOURCE_REGISTRY_HEADER = [
    "source_id",
    "institution",
    "source_title",
    "url",
    "source_type",
    "evidence_strength",
    "key_claim_or_signal",
    "signal_engine_use_case",
    "rights_usage_note",
    "claim_limit",
    "status",
]
FEATURE_BACKLOG_HEADER = [
    "feature_id",
    "feature_family",
    "feature_name",
    "description",
    "source_signal",
    "label_targets",
    "required_inputs",
    "output_object",
    "training_value",
    "rights_risk",
    "priority",
    "status",
]
DATASET_TARGETS_HEADER = [
    "dataset_id",
    "dataset_name",
    "dataset_type",
    "source_examples",
    "rights_status",
    "raw_text_allowed_in_repo",
    "training_allowed",
    "primary_use",
    "required_fields",
    "blocked_conditions",
    "priority",
    "status",
]

SOURCE_REQUIRED_IDS = {
    "man_alphagpt_official",
    "man_alphagpt_external_reporting",
    "point72_cubist_ml_role",
    "deshaw_applied_ai_engineer",
    "deshaw_ml_researcher",
    "deshaw_quant_analyst",
    "citadel_alt_data_research",
    "citadel_securities_economics_intelligence",
    "ssrn_llm_quant_practitioner_guide",
    "alpha_gpt_academic_framework",
    "emnlp_llm_strategy_discovery",
    "earnings_call_rag_or_report_analysis_1",
    "earnings_call_rag_or_report_analysis_2",
    "earnings_call_structured_reasoning",
}
FEATURE_REQUIRED_IDS = {
    "guidance_prior_current_value_match",
    "guidance_direction_classifier",
    "guidance_topic_normalizer",
    "analyst_challenge_question_detector",
    "analyst_followup_pressure_detector",
    "management_non_answer_detector",
    "management_hedging_phrase_detector",
    "uncertainty_safe_harbor_filter",
    "uncertainty_business_risk_detector",
    "reassurance_confidence_phrase_detector",
    "answer_shift_prepared_vs_qa_detector",
    "evidence_span_completeness_score",
    "speaker_role_confidence_score",
    "section_classifier",
    "qa_pair_extractor",
    "false_positive_safe_harbor_detector",
    "retrieval_evidence_object_builder",
    "event_aligned_chunk_builder",
    "semantic_chunk_builder",
    "retail_baseline_timer",
    "reviewer_disagreement_flag",
    "post_call_market_reaction_metadata_join",
    "audio_pause_metadata_flag",
    "audio_speech_rate_metadata_flag",
    "video_keyframe_window_flag",
}
DATASET_REQUIRED_IDS = {
    "manual_local_rights_cleared_transcripts_30_call_pilot",
    "manual_local_rights_cleared_transcripts_100_150_call_corpus",
    "five_hundred_call_metadata_universe",
    "company_ir_transcripts",
    "sec_edgar_8k_earnings_exhibits",
    "sec_edgar_10q_10k_guidance_context",
    "earnings_press_releases",
    "stock_price_reaction_metadata",
    "analyst_estimate_revision_metadata",
    "human_review_gold_labels",
    "weak_label_candidates",
    "retrieval_evidence_objects",
    "audio_metadata_optional",
    "video_metadata_optional",
    "external_academic_datasets_metadata_only",
    "licensed_vendor_transcripts_if_authorized",
}

SOURCE_EVIDENCE_STRENGTH = {
    "strong_public_evidence",
    "public_reporting",
    "job_post_signal",
    "academic_reference",
    "inference_only",
    "pending_verification",
}
SOURCE_STATUS = {
    "verified_from_provided_source",
    "needs_manual_verification",
    "source_unavailable",
    "do_not_use_as_claim",
}
FEATURE_FAMILIES = {
    "guidance_revision",
    "analyst_pressure",
    "management_hedging",
    "uncertainty",
    "reassurance",
    "answer_shift",
    "evidence_quality",
    "retrieval",
    "evaluation",
    "event_study",
    "audio_optional",
    "video_optional",
}
FEATURE_STATUS = {"planned", "candidate", "blocked_until_data", "later_optional"}
RIGHTS_RISK = {
    "low",
    "medium",
    "high",
    "local_only",
    "metadata_only",
    "license_required",
    "rights_cleared_required",
    "low_metadata_only",
    "medium_local_text",
    "metadata_vendor_or_public",
}
RAW_TEXT_ALLOWED = {"yes", "no", "metadata_only", "local_only"}
TRAINING_ALLOWED = {
    "yes_if_rights_cleared",
    "no",
    "metadata_only",
    "license_required",
    "local_only",
}

PLACEHOLDERS = [
    "tbd",
    "todo",
    "lorem ipsum",
    "fixme",
    "xxx",
]
SPEAKER_BLOCKS = [
    "Operator:",
    "Analyst:",
    "Chief Financial Officer:",
    "Prepared Remarks:",
]
UNSUPPORTED_CLAIMS = [
    "guaranteed alpha",
    "proven alpha",
    "predicts stock moves",
    "buy signal",
    "sell signal",
    "trading recommendation",
    "live trading system",
]
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def new_result() -> dict:
    return {
        "ok": True,
        "files_checked": [],
        "errors": [],
        "warnings": [],
        "row_counts": {},
    }


def merge_result(target: dict, source: dict) -> dict:
    target["files_checked"].extend(source["files_checked"])
    target["errors"].extend(source["errors"])
    target["warnings"].extend(source["warnings"])
    target["row_counts"].update(source["row_counts"])
    target["ok"] = not target["errors"]
    return target


def add_error(errors: list[dict], path: str, reason: str, row: int | None = None, field: str | None = None) -> None:
    parts = [path]
    if row is not None:
        parts.append(f"row {row}")
    if field is not None:
        parts.append(f"field {field}")
    parts.append(reason)
    errors.append(
        {
            "path": path,
            "row": row,
            "field": field,
            "reason": reason,
            "message": ": ".join(parts),
        }
    )


def load_csv(path: str | Path) -> dict:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = list(reader.fieldnames or [])
        rows = []
        for row_number, row in enumerate(reader, start=2):
            copied = dict(row)
            copied["__row_number"] = row_number
            rows.append(copied)
    return {"path": str(csv_path), "headers": headers, "rows": rows}


def validate_headers(path: str, actual: list[str], expected: list[str], errors: list[dict]) -> None:
    if actual != expected:
        add_error(
            errors,
            path,
            f"exact header mismatch; expected {','.join(expected)}",
            field="header",
        )


def validate_unique_ids(path: str, rows: list[dict], id_field: str, errors: list[dict]) -> None:
    seen: dict[str, int] = {}
    for row in rows:
        row_number = row["__row_number"]
        value = (row.get(id_field) or "").strip()
        if not value:
            continue
        if value in seen:
            add_error(
                errors,
                path,
                f"duplicate {id_field}: {value}; first seen on row {seen[value]}",
                row_number,
                id_field,
            )
        else:
            seen[value] = row_number


def validate_required_ids(path: str, rows: list[dict], id_field: str, required_ids: set[str], errors: list[dict]) -> None:
    present = {(row.get(id_field) or "").strip() for row in rows}
    for required_id in sorted(required_ids - present):
        add_error(errors, path, f"missing required {id_field}: {required_id}", field=id_field)


def validate_enum_values(path: str, rows: list[dict], field: str, allowed: set[str], errors: list[dict]) -> None:
    for row in rows:
        value = (row.get(field) or "").strip()
        if value and value not in allowed:
            add_error(
                errors,
                path,
                f"invalid enum value {value!r}; allowed values: {', '.join(sorted(allowed))}",
                row["__row_number"],
                field,
            )


def validate_required_fields(path: str, rows: list[dict], fields: list[str], errors: list[dict]) -> None:
    for row in rows:
        for field in fields:
            if not (row.get(field) or "").strip():
                add_error(errors, path, "required field is empty", row["__row_number"], field)


def row_text(row: dict) -> str:
    return " ".join(str(value or "") for key, value in row.items() if not key.startswith("__"))


def row_allows_local_path(row: dict) -> bool:
    lowered = row_text(row).lower()
    return "local_only" in lowered or "local-only" in lowered


def validate_general_safety(path: str, rows: list[dict], fields: list[str], errors: list[dict]) -> None:
    for row in rows:
        row_number = row["__row_number"]
        for field in fields:
            value = row.get(field) or ""
            stripped = value.strip()
            lowered = stripped.lower()
            if len(stripped) > 1000:
                add_error(errors, path, "cell exceeds 1,000 characters", row_number, field)
            for placeholder in PLACEHOLDERS:
                if re.search(rf"\b{re.escape(placeholder)}\b", lowered):
                    add_error(errors, path, f"placeholder value remains: {placeholder}", row_number, field)
            for block in SPEAKER_BLOCKS:
                if block.lower() in lowered:
                    add_error(errors, path, f"raw transcript-like speaker block found: {block}", row_number, field)
            for claim in UNSUPPORTED_CLAIMS:
                if claim in lowered:
                    add_error(errors, path, f"unsupported claim language found: {claim}", row_number, field)
            if looks_like_local_path(stripped) and not row_allows_local_path(row):
                add_error(errors, path, "local absolute path is not clearly marked local-only", row_number, field)


def looks_like_local_path(value: str) -> bool:
    return bool(
        value.startswith("/")
        or value.startswith("~/")
        or re.match(r"^[A-Za-z]:[\\/]", value)
        or value.startswith("file://")
    )


def validate_minimum_rows(path: str, rows: list[dict], minimum: int, errors: list[dict]) -> None:
    if len(rows) < minimum:
        add_error(errors, path, f"expected at least {minimum} rows, found {len(rows)}")


def finalize_result(result: dict) -> dict:
    result["ok"] = not result["errors"]
    return result


def validate_source_registry(repo_root: str | Path, path_override: str | Path | None = None) -> dict:
    result = new_result()
    repo = Path(repo_root)
    path = Path(path_override) if path_override is not None else repo / SOURCE_REGISTRY_PATH
    display_path = SOURCE_REGISTRY_PATH if path_override is None else str(path)
    result["files_checked"].append(display_path)
    loaded = load_csv(path)
    rows = loaded["rows"]
    result["row_counts"][display_path] = len(rows)
    errors = result["errors"]

    validate_headers(display_path, loaded["headers"], SOURCE_REGISTRY_HEADER, errors)
    validate_minimum_rows(display_path, rows, 14, errors)
    validate_required_fields(display_path, rows, SOURCE_REGISTRY_HEADER, errors)
    validate_unique_ids(display_path, rows, "source_id", errors)
    validate_required_ids(display_path, rows, "source_id", SOURCE_REQUIRED_IDS, errors)
    validate_enum_values(display_path, rows, "evidence_strength", SOURCE_EVIDENCE_STRENGTH, errors)
    validate_enum_values(display_path, rows, "status", SOURCE_STATUS, errors)
    validate_general_safety(display_path, rows, SOURCE_REGISTRY_HEADER, errors)

    for row in rows:
        row_number = row["__row_number"]
        source_id = (row.get("source_id") or "").strip()
        status = (row.get("status") or "").strip()
        url = (row.get("url") or "").strip()
        evidence_strength = (row.get("evidence_strength") or "").strip()
        all_text = row_text(row).lower()
        claim_limit = (row.get("claim_limit") or "").lower()

        if not url and status != "source_unavailable":
            add_error(errors, display_path, "empty url allowed only when status=source_unavailable", row_number, "url")
        if url and not url.startswith("https://"):
            add_error(errors, display_path, "url must start with https://", row_number, "url")
        if looks_like_local_path(url):
            add_error(errors, display_path, "url must not be a local file path", row_number, "url")

        if source_id == "man_alphagpt_external_reporting":
            has_external = "external reporting" in all_text or evidence_strength == "public_reporting"
            has_not_official = (
                "not man-official" in all_text
                or "not independently" in all_text
                or ("independently verified" in claim_limit and "do not" in claim_limit)
            )
            if not (has_external and has_not_official):
                add_error(
                    errors,
                    display_path,
                    "claim_limit must label AlphaGPT live-signal claim as external reporting and not Man-official confirmation",
                    row_number,
                    "claim_limit",
                )

        if evidence_strength == "public_reporting":
            official_claim = "official confirmation" in all_text and "not" not in all_text
            if official_claim:
                add_error(
                    errors,
                    display_path,
                    "public reporting row must not present external report as official confirmation",
                    row_number,
                    "claim_limit",
                )

        if evidence_strength == "academic_reference":
            risky_live_claim = (
                "proves live trading performance" in all_text
                or "proof of live trading performance" in all_text
                and "not proof" not in all_text
            )
            if risky_live_claim:
                add_error(
                    errors,
                    display_path,
                    "academic reference must not claim live trading performance",
                    row_number,
                    "claim_limit",
                )

    return finalize_result(result)


def validate_feature_backlog(repo_root: str | Path, path_override: str | Path | None = None) -> dict:
    result = new_result()
    repo = Path(repo_root)
    path = Path(path_override) if path_override is not None else repo / FEATURE_BACKLOG_PATH
    display_path = FEATURE_BACKLOG_PATH if path_override is None else str(path)
    result["files_checked"].append(display_path)
    loaded = load_csv(path)
    rows = loaded["rows"]
    result["row_counts"][display_path] = len(rows)
    errors = result["errors"]

    validate_headers(display_path, loaded["headers"], FEATURE_BACKLOG_HEADER, errors)
    validate_minimum_rows(display_path, rows, 30, errors)
    validate_required_fields(display_path, rows, FEATURE_BACKLOG_HEADER, errors)
    validate_unique_ids(display_path, rows, "feature_id", errors)
    validate_required_ids(display_path, rows, "feature_id", FEATURE_REQUIRED_IDS, errors)
    validate_enum_values(display_path, rows, "feature_family", FEATURE_FAMILIES, errors)
    validate_enum_values(display_path, rows, "status", FEATURE_STATUS, errors)
    validate_enum_values(display_path, rows, "rights_risk", RIGHTS_RISK, errors)
    validate_general_safety(display_path, rows, FEATURE_BACKLOG_HEADER, errors)

    families = {(row.get("feature_family") or "").strip() for row in rows}
    for family in sorted(FEATURE_FAMILIES - families):
        add_error(errors, display_path, f"missing required feature_family coverage: {family}", field="feature_family")

    for row in rows:
        row_number = row["__row_number"]
        feature_id = (row.get("feature_id") or "").strip()
        label_targets = (row.get("label_targets") or "").strip()
        support_text = row_text(row).lower()
        if feature_id and not SNAKE_CASE.match(feature_id):
            add_error(errors, display_path, "feature_id must be snake_case", row_number, "feature_id")
        if not label_targets and not any(
            marker in support_text for marker in ("non_label_support", "metadata_support", "evaluation_support")
        ):
            add_error(
                errors,
                display_path,
                "label_targets must be non-empty or explicitly contain non_label_support, metadata_support, or evaluation_support",
                row_number,
                "label_targets",
            )

    return finalize_result(result)


def validate_dataset_targets(repo_root: str | Path, path_override: str | Path | None = None) -> dict:
    result = new_result()
    repo = Path(repo_root)
    path = Path(path_override) if path_override is not None else repo / DATASET_TARGETS_PATH
    display_path = DATASET_TARGETS_PATH if path_override is None else str(path)
    result["files_checked"].append(display_path)
    loaded = load_csv(path)
    rows = loaded["rows"]
    result["row_counts"][display_path] = len(rows)
    errors = result["errors"]

    validate_headers(display_path, loaded["headers"], DATASET_TARGETS_HEADER, errors)
    validate_minimum_rows(display_path, rows, 16, errors)
    validate_required_fields(display_path, rows, DATASET_TARGETS_HEADER, errors)
    validate_unique_ids(display_path, rows, "dataset_id", errors)
    validate_required_ids(display_path, rows, "dataset_id", DATASET_REQUIRED_IDS, errors)
    validate_enum_values(display_path, rows, "raw_text_allowed_in_repo", RAW_TEXT_ALLOWED, errors)
    validate_enum_values(display_path, rows, "training_allowed", TRAINING_ALLOWED, errors)
    validate_general_safety(display_path, rows, DATASET_TARGETS_HEADER, errors)

    by_id = {(row.get("dataset_id") or "").strip(): row for row in rows}
    vendor = by_id.get("licensed_vendor_transcripts_if_authorized")
    if vendor and vendor.get("training_allowed") != "license_required":
        add_error(
            errors,
            display_path,
            "licensed vendor transcripts require restrictive training permission",
            vendor["__row_number"],
            "training_allowed",
        )

    academic = by_id.get("external_academic_datasets_metadata_only")
    if academic and academic.get("raw_text_allowed_in_repo") not in {"metadata_only", "no"}:
        add_error(
            errors,
            display_path,
            "external academic datasets metadata-only target must not allow raw text in repo",
            academic["__row_number"],
            "raw_text_allowed_in_repo",
        )

    market = by_id.get("stock_price_reaction_metadata")
    if market:
        text = row_text(market).lower()
        if "event-study" not in text and "event study" not in text and "evaluation" not in text:
            add_error(
                errors,
                display_path,
                "stock price reaction metadata must be framed as evaluation/event-study metadata",
                market["__row_number"],
                "primary_use",
            )
        if "extraction target" in text or "target leakage" in text and "not" not in text:
            add_error(
                errors,
                display_path,
                "stock price reaction metadata must not be extraction target leakage",
                market["__row_number"],
                "primary_use",
            )

    weak = by_id.get("weak_label_candidates")
    if weak and "gold" in row_text(weak).lower() and "gold labels" in row_text(weak).lower() and "auto-promoted" not in row_text(weak).lower():
        add_error(
            errors,
            display_path,
            "weak label candidates must not be treated as gold labels",
            weak["__row_number"],
            "primary_use",
        )

    gold = by_id.get("human_review_gold_labels")
    if gold and "reviewer" not in (gold.get("required_fields") or "").lower():
        add_error(
            errors,
            display_path,
            "human_review_gold_labels must require reviewer fields",
            gold["__row_number"],
            "required_fields",
        )

    for dataset_id in (
        "manual_local_rights_cleared_transcripts_30_call_pilot",
        "manual_local_rights_cleared_transcripts_100_150_call_corpus",
    ):
        row = by_id.get(dataset_id)
        if not row:
            continue
        raw_allowed = row.get("raw_text_allowed_in_repo")
        training_allowed = row.get("training_allowed")
        if raw_allowed not in {"local_only", "metadata_only"}:
            add_error(
                errors,
                display_path,
                "manual-local transcript datasets must keep raw text local-only or metadata-only",
                row["__row_number"],
                "raw_text_allowed_in_repo",
            )
        if training_allowed != "yes_if_rights_cleared":
            add_error(
                errors,
                display_path,
                "manual-local transcript datasets must require rights-cleared training permission",
                row["__row_number"],
                "training_allowed",
            )

    return finalize_result(result)


def validate_all(repo_root: str | Path = ".") -> dict:
    result = new_result()
    for validator in (validate_source_registry, validate_feature_backlog, validate_dataset_targets):
        merge_result(result, validator(repo_root))
    return finalize_result(result)


def print_human(result: dict) -> None:
    if result["ok"]:
        print("Research registry validation passed.")
    else:
        print("Research registry validation failed.")
    for path in result["files_checked"]:
        count = result["row_counts"].get(path)
        print(f"- {path}: {count} rows")
    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"- {error['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root containing data/research CSVs.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    result = validate_all(Path(args.repo_root))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
