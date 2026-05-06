#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
SRC = ROOT / "src"
for path in (TOOLS, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from priority_review_common import (  # noqa: E402
    FALSE_POSITIVE_RE,
    GOLD_PATH,
    GUIDANCE_RE,
    LABELS,
    MANIFEST_PATH,
    NEUTRAL_STATUS_RE,
    PACKET_CSV,
    PACKET_MD,
    PRESSURE_RE,
    PRIORITY_1_CALLS,
    PRIORITY_2_TICKERS,
    REVIEW_FIELDS,
    UNCERTAINTY_RE,
    case_paths,
    gold_fingerprints,
    manifest_by_case,
    norm_text,
    read_jsonl,
    target_manual_path,
    write_csv,
)
from signal_engine.signal_baseline import predict_deterministic_signal_family  # noqa: E402

REPORTS = ROOT / "reports"


def optional_ml_predictions(texts: list[str]) -> list[str]:
    gold_rows = [row for row in read_jsonl(GOLD_PATH) if row.get("signal_family") in LABELS and row.get("text")]
    labels = [str(row["signal_family"]) for row in gold_rows]
    if len(set(labels)) < 2 or not texts:
        return [""] * len(texts)
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except Exception:
        return [""] * len(texts)
    try:
        model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ("clf", LogisticRegression(max_iter=500, random_state=42, class_weight="balanced")),
            ]
        )
        model.fit([str(row["text"]) for row in gold_rows], labels)
        return [str(value) for value in model.predict(texts)]
    except Exception:
        return [""] * len(texts)


def evidence_rows_for_case(case_id: str) -> list[dict[str, Any]]:
    paths = case_paths(case_id, manifest_by_case().get(case_id))
    evidence_path = paths["evidence_objects"]
    rows = read_jsonl(Path(evidence_path)) if evidence_path else []
    if len(rows) >= 20:
        return rows
    raw_path = paths["raw_transcript"]
    if not raw_path:
        return rows
    words = str(Path(raw_path).read_text(encoding="utf-8", errors="ignore")).split()
    transcript_rows: list[dict[str, Any]] = []
    window_size = 55
    step = 38
    for index, start in enumerate(range(0, max(0, len(words) - window_size + 1), step)):
        window = " ".join(words[start : start + window_size]).strip()
        if len(window) < 80:
            continue
        transcript_rows.append(
            {
                "case_id": case_id,
                "object_id": f"{case_id}_transcript_window_{index:04d}",
                "section": "raw_transcript_window",
                "speaker": "",
                "speaker_role": "",
                "text": window,
            }
        )
        if len(transcript_rows) >= 160:
            break
    return [*rows, *transcript_rows]


def alternative_label(text: str, predicted_label: str) -> str:
    if UNCERTAINTY_RE.search(text) and predicted_label == "opportunity_commitment":
        return "uncertainty_hedging"
    if NEUTRAL_STATUS_RE.search(text) and predicted_label != "neutral":
        return "neutral"
    if GUIDANCE_RE.search(text) and predicted_label == "neutral":
        return "uncertainty_hedging"
    if PRESSURE_RE.search(text) and predicted_label == "neutral":
        return "risk_friction"
    return ""


def priority_reason(text: str, prediction: dict[str, Any], ml_prediction: str, counts: Counter[str]) -> tuple[int, list[str]]:
    predicted_label = str(prediction.get("label") or "neutral")
    reasons: list[str] = []
    score = 0
    if counts.get(predicted_label, 0) < max(counts.values() or [0]):
        score += 20
        reasons.append("underrepresented_label")
    if ml_prediction and ml_prediction != predicted_label:
        score += 30
        reasons.append("deterministic_vs_ml_disagreement")
    if FALSE_POSITIVE_RE.search(text):
        score += 18
        reasons.append("false_positive_prone_trigger")
    if GUIDANCE_RE.search(text):
        score += 18
        reasons.append("guidance_outlook_language")
    if PRESSURE_RE.search(text):
        score += 14
        reasons.append("analyst_pressure_or_qa_friction")
    if UNCERTAINTY_RE.search(text):
        score += 16
        reasons.append("uncertainty_vs_opportunity_confusion")
    if NEUTRAL_STATUS_RE.search(text):
        score += 12
        reasons.append("neutral_operational_status_confusion")
    evidence_terms = prediction.get("evidence_terms") or []
    if evidence_terms:
        score += min(12, len(evidence_terms) * 3)
        reasons.append("deterministic_trigger_present")
    if not reasons:
        reasons.append("coverage_sample")
    return score, reasons


def candidate_pool() -> list[dict[str, Any]]:
    gold_rows = read_jsonl(GOLD_PATH)
    fingerprints = gold_fingerprints(gold_rows)
    label_counts = Counter(str(row.get("signal_family") or "") for row in gold_rows)
    raw_candidates: list[dict[str, Any]] = []
    seen_texts: set[tuple[str, str]] = set()
    for call in PRIORITY_1_CALLS:
        case_id = call["case_id"]
        paths = case_paths(case_id, manifest_by_case().get(case_id))
        source_path = paths["evidence_objects"]
        for row in evidence_rows_for_case(case_id):
            text = str(row.get("text") or "").strip()
            if len(text) < 40 or len(text) > 700:
                continue
            if norm_text(text) in {"thank you.", "good morning.", "good afternoon."}:
                continue
            key = (case_id, norm_text(text))
            if key in seen_texts:
                continue
            seen_texts.add(key)
            prediction = predict_deterministic_signal_family(text)
            predicted_label = str(prediction.get("label") or "neutral")
            if (case_id, norm_text(text), predicted_label) in fingerprints or ("", norm_text(text), predicted_label) in fingerprints:
                continue
            raw_candidates.append(
                {
                    "case_id": case_id,
                    "ticker": call["ticker"],
                    "fiscal_period": call["fiscal_period"],
                    "source_path": str(source_path.relative_to(ROOT)) if source_path else "",
                    "section": row.get("section") or "",
                    "speaker": row.get("speaker") or row.get("speaker_role") or "",
                    "evidence_text": text,
                    "prediction": prediction,
                }
            )
    ml_predictions = optional_ml_predictions([row["evidence_text"] for row in raw_candidates])
    for row, ml_prediction in zip(raw_candidates, ml_predictions, strict=False):
        predicted_label = str(row["prediction"].get("label") or "neutral")
        score, reasons = priority_reason(row["evidence_text"], row["prediction"], ml_prediction, label_counts)
        row["predicted_label"] = predicted_label
        row["alternative_label_if_ambiguous"] = alternative_label(row["evidence_text"], predicted_label)
        row["trigger_terms"] = "; ".join(str(term) for term in row["prediction"].get("evidence_terms") or [])
        row["deterministic_confidence"] = row["prediction"].get("confidence") or 0.0
        row["ml_prediction_if_available"] = ml_prediction
        row["disagreement_flag"] = "yes" if ml_prediction and ml_prediction != predicted_label else "no"
        row["review_priority_score"] = score
        row["review_priority_reason"] = "; ".join(reasons)
    return raw_candidates


def select_balanced_batch(candidates: list[dict[str, Any]], per_call: int = 12) -> list[dict[str, Any]]:
    by_call: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_call[str(row["case_id"])].append(row)
    selected: list[dict[str, Any]] = []
    for call in PRIORITY_1_CALLS:
        rows = sorted(by_call.get(call["case_id"], []), key=lambda row: (-int(row.get("review_priority_score") or 0), row["evidence_text"]))
        chosen: list[dict[str, Any]] = []
        per_label_seen: Counter[str] = Counter()
        for row in rows:
            label = str(row.get("predicted_label") or "neutral")
            if per_label_seen[label] < 3:
                chosen.append(row)
                per_label_seen[label] += 1
            if len(chosen) >= per_call:
                break
        if len(chosen) < per_call:
            chosen_keys = {norm_text(row["evidence_text"]) for row in chosen}
            for row in rows:
                if norm_text(row["evidence_text"]) not in chosen_keys:
                    chosen.append(row)
                    chosen_keys.add(norm_text(row["evidence_text"]))
                if len(chosen) >= per_call:
                    break
        selected.extend(chosen)
    for index, row in enumerate(selected, start=1):
        row["review_id"] = f"priority_review_{index:04d}"
        row["reviewer_decision"] = ""
        row["corrected_label"] = ""
        row["reviewer_notes"] = ""
    return selected


def inventory_rows() -> list[dict[str, Any]]:
    manifest = manifest_by_case()
    gold_rows = read_jsonl(GOLD_PATH)
    rows: list[dict[str, Any]] = []
    for call in PRIORITY_1_CALLS:
        case_id = call["case_id"]
        paths = case_paths(case_id, manifest.get(case_id))
        evidence_rows = evidence_rows_for_case(case_id)
        gold_for_case = [row for row in gold_rows if str(row.get("case_id") or "") == case_id]
        labels = sorted({str(row.get("signal_family") or row.get("label") or "") for row in gold_for_case if row.get("signal_family") or row.get("label")})
        transcript_present = bool(paths["raw_transcript"])
        processed_present = bool(paths["evidence_objects"] or paths["event_chunks"] or paths["sectioned"])
        candidate_count = len([row for row in evidence_rows if 40 <= len(str(row.get("text") or "")) <= 700])
        if processed_present and candidate_count:
            action = "review now"
            score = 100
        elif transcript_present:
            action = "process transcript"
            score = 70
        else:
            action = "download transcript"
            score = 20
        rows.append(
            {
                "priority": "1",
                "requested_case_id": call["requested_case_id"],
                "case_id": case_id,
                "ticker": call["ticker"],
                "fiscal_period": call["fiscal_period"],
                "transcript_present": "yes" if transcript_present else "no",
                "raw_transcript_path": str(paths["raw_transcript"].relative_to(ROOT)) if paths["raw_transcript"] else "",
                "processed_outputs_present": "yes" if processed_present else "no",
                "candidate_labels_present": "yes" if candidate_count else "no",
                "existing_canonical_gold_labels": len(gold_for_case),
                "reviewed_labels_count": sum(1 for row in gold_for_case if row.get("label_source") == "human_reviewed_priority_packet"),
                "estimated_candidate_count": candidate_count,
                "label_types_represented": ", ".join(labels),
                "review_priority_score": score,
                "recommended_action": action,
            }
        )
    for ticker in PRIORITY_2_TICKERS:
        case_id = f"{ticker}_2025_Q4_priority_review"
        paths = case_paths(case_id)
        rows.append(
            {
                "priority": "2",
                "requested_case_id": case_id,
                "case_id": case_id,
                "ticker": ticker,
                "fiscal_period": "Q4_2025",
                "transcript_present": "yes" if paths["raw_transcript"] else "no",
                "raw_transcript_path": str(paths["raw_transcript"].relative_to(ROOT)) if paths["raw_transcript"] else "",
                "processed_outputs_present": "yes" if paths["evidence_objects"] else "no",
                "candidate_labels_present": "no",
                "existing_canonical_gold_labels": 0,
                "reviewed_labels_count": 0,
                "estimated_candidate_count": 0,
                "label_types_represented": "",
                "review_priority_score": 40,
                "recommended_action": "download transcript",
            }
        )
    return rows


def write_inventory(rows: list[dict[str, Any]]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Call Review Inventory",
        "",
        "This inventory is generated from committed manifests, raw transcript paths, processed evidence objects, and canonical gold labels.",
        "",
        "| priority | case | ticker | transcript | raw path | processed | candidates | gold | reviewed | estimated candidates | labels | score | action |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['priority']} | `{row['case_id']}` | {row['ticker']} | {row['transcript_present']} | "
            f"`{row['raw_transcript_path']}` | {row['processed_outputs_present']} | {row['candidate_labels_present']} | "
            f"{row['existing_canonical_gold_labels']} | {row['reviewed_labels_count']} | {row['estimated_candidate_count']} | "
            f"{row['label_types_represented']} | {row['review_priority_score']} | {row['recommended_action']} |"
        )
    (REPORTS / "call_review_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_download_plan(rows: list[dict[str, Any]]) -> None:
    missing = [row for row in rows if row["transcript_present"] == "no"]
    lines = [
        "# Transcript Download Plan",
        "",
        "No gated or paywalled transcripts should be downloaded silently. Use company investor relations, SEC 8-K exhibits where available, or legally usable public sources.",
        "",
        "| priority | ticker | target case_id | target path | suggested source type | why it matters |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in missing:
        target_path = target_manual_path(str(row["case_id"]))
        why = "Priority 1 benchmark coverage" if row["priority"] == "1" else "Priority 2 label diversity and 150-250 label scaling"
        lines.append(
            f"| {row['priority']} | {row['ticker']} | `{row['case_id']}` | `{target_path}` | "
            "company IR transcript, SEC 8-K exhibit, or legally usable public transcript | "
            f"{why} |"
        )
    lines.extend(
        [
            "",
            "## Manual Instructions",
            "",
            "1. Confirm the source is public and legally usable.",
            "2. Save the transcript text to the target path shown above.",
            "3. Keep source URL and license/provenance notes beside the manual case README.",
            "4. Process the transcript through the existing deterministic corpus workflow before mining labels.",
        ]
    )
    (REPORTS / "transcript_download_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_packet_markdown(rows: list[dict[str, Any]]) -> None:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_case[str(row["case_id"])].append(row)
    lines = [
        "# Priority Review Packet",
        "",
        "Review goal: accept only clear evidence, reject vague/generic language, correct labels when needed, and mark unclear when uncertain.",
        "",
        "Allowed labels: `risk_friction`, `opportunity_commitment`, `uncertainty_hedging`, `neutral`.",
        "",
        "Reviewer decisions: `accept`, `reject`, or `unclear`.",
        "",
    ]
    for call in PRIORITY_1_CALLS:
        case_rows = by_case.get(call["case_id"], [])
        if not case_rows:
            lines.extend([f"## {call['case_id']}", "", "No review-ready candidates found.", ""])
            continue
        lines.extend([f"## {call['case_id']} ({call['ticker']} {call['fiscal_period']})", ""])
        for row in case_rows[:12]:
            lines.extend(
                [
                    f"### {row['review_id']}",
                    "",
                    f"- predicted_label: `{row['predicted_label']}`",
                    f"- alternative_label_if_ambiguous: `{row['alternative_label_if_ambiguous']}`",
                    f"- reason: {row['review_priority_reason']}",
                    f"- trigger_terms: `{row['trigger_terms']}`",
                    f"- confidence: `{row['deterministic_confidence']}`",
                    f"- text: {row['evidence_text']}",
                    "",
                ]
            )
        if len(case_rows) > 12:
            lines.extend([f"_Additional overflow candidates for this call are available in the CSV: {len(case_rows) - 12} rows._", ""])
    PACKET_MD.parent.mkdir(parents=True, exist_ok=True)
    PACKET_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_status(packet_rows: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> None:
    ready = [row for row in inventory if row["priority"] == "1" and row["recommended_action"] == "review now"]
    missing = [row for row in inventory if row["priority"] == "1" and row["recommended_action"] == "download transcript"]
    by_case = Counter(str(row["case_id"]) for row in packet_rows)
    labels = Counter(str(row["predicted_label"]) for row in packet_rows)
    lines = [
        "# Priority Review Status",
        "",
        f"- packet_rows: `{len(packet_rows)}`",
        f"- ready_priority_1_calls: `{len(ready)}`",
        f"- missing_priority_1_transcripts: `{len(missing)}`",
        f"- expected_accepts_if_6_per_ready_call: `{len(ready) * 6}`",
        f"- expected_accepts_if_8_per_ready_call: `{len(ready) * 8}`",
        "",
        "## Rows By Call",
        "",
        *[f"- `{case_id}`: {count}" for case_id, count in sorted(by_case.items())],
        "",
        "## Predicted Label Mix",
        "",
        *[f"- `{label}`: {count}" for label, count in sorted(labels.items())],
        "",
        "## Ready Now",
        "",
        *[f"- `{row['case_id']}`" for row in ready],
        "",
        "## Needs Transcript Download",
        "",
        *[f"- `{row['case_id']}` -> `{target_manual_path(str(row['case_id']))}`" for row in missing],
    ]
    (REPORTS / "priority_review_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a human review packet for priority earnings-call labels.")
    parser.add_argument("--per-call", type=int, default=18)
    args = parser.parse_args(argv)

    if not MANIFEST_PATH.exists():
        raise SystemExit(f"missing manifest: {MANIFEST_PATH}")
    inventory = inventory_rows()
    candidates = candidate_pool()
    packet_rows = select_balanced_batch(candidates, per_call=args.per_call)
    write_csv(PACKET_CSV, packet_rows, REVIEW_FIELDS)
    write_packet_markdown(packet_rows)
    write_inventory(inventory)
    write_download_plan(inventory)
    write_status(packet_rows, inventory)
    print(json.dumps({"status": "ok", "packet_rows": len(packet_rows), "csv": str(PACKET_CSV), "markdown": str(PACKET_MD)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
