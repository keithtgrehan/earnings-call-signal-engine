#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation_backbone import (
    confidence_bucket,
    load_jsonl,
    text_length_bucket,
    top_two_labels,
    top_two_margin,
    write_csv,
    write_json,
)
from signal_engine.signal_baseline import HUMAN_REVIEWED_LABELS_RELATIVE_PATH

GENERIC_OPERATIONAL_TERMS = {"renewal", "procurement", "send", "meeting", "review"}


def _display_path(path: Path) -> str:
    if path.is_absolute():
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _load_labels(path: Path) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in load_jsonl(path)}


def _primary_actions(row: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if row["both_wrong"]:
        actions.extend(["needs_second_reviewer", "hold_for_gold_set_review"])
    elif row["classifier_only_correct"]:
        actions.append("tighten_lexicon_term")
    elif row["rules_only_correct"]:
        actions.append("benchmark_only_no_label_change")
    if row["gold_label"] == "neutral" and (
        row["deterministic_label"] != "neutral" or row["classifier_label"] != "neutral"
    ):
        actions.append("improve_neutral_examples")
    if row["gold_label"] == "uncertainty_hedging" and row["deterministic_label"] != row["gold_label"]:
        actions.append("review_conditionals_and_hedges")
    if any(term in GENERIC_OPERATIONAL_TERMS for term in row["deterministic_evidence_terms"]):
        actions.append("tighten_lexicon_term")
    if row["ambiguous_or_low_confidence"]:
        actions.append("needs_second_reviewer")
    ordered: list[str] = []
    for action in actions or ["no_action_clear_ok"]:
        if action not in ordered:
            ordered.append(action)
    return ordered


def _priority_score(row: dict[str, Any]) -> int:
    score = 0
    if row["both_wrong"]:
        score += 5
    if row["classifier_only_correct"] or row["rules_only_correct"]:
        score += 3
    if row["ambiguous_or_low_confidence"]:
        score += 2
    if row["text_length_bucket"] == "short":
        score += 1
    return score


def _priority_reason(row: dict[str, Any], actions: list[str]) -> str:
    reasons: list[str] = []
    if row["both_wrong"]:
        reasons.append("both systems miss the gold label")
    elif row["classifier_only_correct"]:
        reasons.append("classifier recovers the gold label where rules miss")
    elif row["rules_only_correct"]:
        reasons.append("rules outperform the selected classifier on this example")
    if row["ambiguous_or_low_confidence"]:
        reasons.append("confidence or evidence pattern looks ambiguous")
    if "improve_neutral_examples" in actions:
        reasons.append("neutral coverage still needs tightening")
    return "; ".join(reasons) if reasons else "clear agreement case"


def _render_report(payload: dict[str, Any]) -> str:
    counts = payload["error_buckets"]["counts"]
    lines = [
        "# Signal Error Analysis",
        "",
        "This is an early error-analysis pass on a small labeled set, not statistical proof.",
        "Deterministic rules remain canonical.",
        "Classifier variants are exploratory benchmark aids only.",
        "",
        "## Dataset And Evaluation Context",
        "",
        f"- dataset_path: `{payload['dataset_path']}`",
        f"- predictions_path: `{payload['predictions_path']}`",
        f"- dataset_size: `{payload['dataset_size']}`",
        f"- evaluation_scope: `{payload['evaluation_scope']}`",
        f"- canonical_system: `{payload['canonical_system']}`",
        "",
        "## Headline Error Counts",
        "",
        f"- deterministic_rule_errors: `{counts['deterministic_rule_errors']}`",
        f"- classifier_errors: `{counts['classifier_errors']}`",
        f"- both_wrong: `{counts['both_wrong']}`",
        f"- classifier_only_correct: `{counts['classifier_only_correct']}`",
        f"- rules_only_correct: `{counts['rules_only_correct']}`",
        f"- ambiguous_or_low_confidence: `{counts['ambiguous_or_low_confidence']}`",
        "",
        "## Baseline Comparison Snapshot",
        "",
        "| system | accuracy | macro_f1 | weighted_f1 |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["benchmark_context"]["benchmark_runs"]:
        metrics = row["metrics"]
        lines.append(
            f"| {row['variant_id']} | {metrics['accuracy']:.4f} | {metrics['macro_f1']:.4f} | {metrics['weighted_f1']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## What The Current Errors Suggest",
            "",
            "- the strongest current rule weakness is uncertainty and neutral overfire, especially when operational terms look like commitment cues",
            "- the classifier helps on some neutral and hedge cases, but still misses clean friction turns",
            "- both-wrong examples are the highest-value second-review candidates",
            "",
            "## Recommended Actions",
            "",
            "| action | count |",
            "| --- | --- |",
        ]
    )
    for action, count in sorted(payload["recommended_action_summary"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {action} | {count} |")
    lines.extend(
        [
            "",
            "## What Not To Conclude",
            "",
            "- This does not prove model superiority.",
            "- This does not prove generalization.",
            "- This does not prove that confidence equals correctness.",
            "",
            "## Next Review Steps",
            "",
            "- review the highest-priority rows in `data/nlp_research/signal_error_analysis.csv`",
            "- send both-wrong and low-confidence cases into second review",
            "- tighten neutral and hedge coverage before making stronger benchmark claims",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze deterministic and classifier errors on the transcript benchmark.")
    parser.add_argument("--labels-path", default=str(ROOT / HUMAN_REVIEWED_LABELS_RELATIVE_PATH))
    parser.add_argument(
        "--predictions-path",
        default=str(ROOT / "data" / "nlp_research" / "transcript_baseline_predictions.jsonl"),
    )
    parser.add_argument(
        "--metrics-path",
        default=str(ROOT / "data" / "nlp_research" / "transcript_baseline_metrics.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(ROOT / "data" / "nlp_research" / "signal_error_analysis.json"),
    )
    parser.add_argument(
        "--csv-out",
        default=str(ROOT / "data" / "nlp_research" / "signal_error_analysis.csv"),
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "signal-error-analysis.md"),
    )
    args = parser.parse_args(argv)
    labels_path = Path(args.labels_path)
    predictions_path = Path(args.predictions_path)
    metrics_path = Path(args.metrics_path)
    json_out = Path(args.json_out)
    csv_out = Path(args.csv_out)
    report_out = Path(args.report_out)

    labels_by_id = _load_labels(labels_path)
    predictions = load_jsonl(predictions_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    grouped = {
        "by_true_label": Counter(),
        "by_predicted_label": Counter(),
        "by_error_pair": Counter(),
        "by_domain": Counter(),
        "by_source_file": Counter(),
        "by_evidence_term": Counter(),
        "by_text_length_bucket": Counter(),
        "by_confidence_bucket": Counter(),
    }
    action_counts = Counter()
    counts = Counter()
    case_rows: list[dict[str, Any]] = []

    for prediction in predictions:
        label_row = labels_by_id[prediction["id"]]
        gold_label = str(prediction["gold_label"])
        deterministic_label = str(prediction["deterministic_label"])
        classifier_label = str(prediction["classifier_label"])
        deterministic_correct = deterministic_label == gold_label
        classifier_correct = classifier_label == gold_label
        score_map = prediction.get("classifier_score_by_label") or {}
        confidence = prediction.get("classifier_confidence")
        top2 = top_two_labels(score_map) if score_map else []
        margin = top_two_margin(score_map) if score_map else None
        evidence_terms = list(prediction.get("deterministic_evidence_terms") or [])
        evidence_count = len(evidence_terms)
        length_bucket = text_length_bucket(prediction["text"])
        conf_bucket = confidence_bucket(confidence if isinstance(confidence, (int, float)) else None)
        ambiguous = (
            (isinstance(confidence, (int, float)) and confidence < 0.40)
            or (margin is not None and margin <= 0.05)
            or evidence_count == 0
            or (evidence_count == 1 and any(term in GENERIC_OPERATIONAL_TERMS for term in evidence_terms))
            or "clause split" in str(label_row.get("notes", "")).lower()
        )
        row = {
            "id": prediction["id"],
            "domain": str(prediction.get("domain") or label_row.get("domain") or ""),
            "source_file": str(prediction.get("source_file") or label_row.get("source_file") or ""),
            "text": prediction["text"],
            "text_length_bucket": length_bucket,
            "gold_label": gold_label,
            "deterministic_label": deterministic_label,
            "deterministic_correct": deterministic_correct,
            "deterministic_evidence_terms": evidence_terms,
            "deterministic_evidence_count": evidence_count,
            "classifier_label": classifier_label,
            "classifier_correct": classifier_correct,
            "classifier_confidence": confidence,
            "classifier_confidence_bucket": conf_bucket,
            "classifier_top2_labels": top2,
            "classifier_margin": round(float(margin), 4) if margin is not None else None,
            "both_wrong": (not deterministic_correct) and (not classifier_correct),
            "classifier_only_correct": classifier_correct and not deterministic_correct,
            "rules_only_correct": deterministic_correct and not classifier_correct,
            "both_correct": deterministic_correct and classifier_correct,
            "ambiguous_or_low_confidence": ambiguous,
            "label_source": str(label_row.get("label_source") or ""),
            "rationale": str(label_row.get("rationale") or ""),
            "notes": str(label_row.get("notes") or ""),
        }
        actions = _primary_actions(row)
        row["recommended_actions"] = actions
        row["priority_score"] = _priority_score(row)
        row["priority_reason"] = _priority_reason(row, actions)
        if row["both_wrong"]:
            row["error_bucket"] = "both_wrong"
        elif row["classifier_only_correct"]:
            row["error_bucket"] = "classifier_only_correct"
        elif row["rules_only_correct"]:
            row["error_bucket"] = "rules_only_correct"
        elif row["ambiguous_or_low_confidence"] and row["both_correct"]:
            row["error_bucket"] = "low_confidence_correct"
        elif row["ambiguous_or_low_confidence"]:
            row["error_bucket"] = "low_confidence_wrong"
        else:
            row["error_bucket"] = "both_correct_clear"
        row["bucket_tags"] = [
            tag
            for tag, enabled in (
                ("both_wrong", row["both_wrong"]),
                ("classifier_only_correct", row["classifier_only_correct"]),
                ("rules_only_correct", row["rules_only_correct"]),
                ("both_correct", row["both_correct"]),
                ("ambiguous_or_low_confidence", row["ambiguous_or_low_confidence"]),
            )
            if enabled
        ]

        grouped["by_true_label"][gold_label] += 1
        grouped["by_predicted_label"][classifier_label] += 1
        grouped["by_error_pair"][f"{gold_label}->{classifier_label}"] += 1
        grouped["by_domain"][row["domain"]] += 1
        grouped["by_source_file"][row["source_file"]] += 1
        grouped["by_text_length_bucket"][length_bucket] += 1
        grouped["by_confidence_bucket"][conf_bucket] += 1
        for term in evidence_terms:
            grouped["by_evidence_term"][term] += 1
        for action in actions:
            action_counts[action] += 1

        counts["total_evaluated"] += 1
        counts["deterministic_rule_errors"] += int(not deterministic_correct)
        counts["classifier_errors"] += int(not classifier_correct)
        counts["both_wrong"] += int(row["both_wrong"])
        counts["classifier_only_correct"] += int(row["classifier_only_correct"])
        counts["rules_only_correct"] += int(row["rules_only_correct"])
        counts["both_correct"] += int(row["both_correct"])
        counts["ambiguous_or_low_confidence"] += int(row["ambiguous_or_low_confidence"])
        case_rows.append(row)

    payload = {
        "status": "ok",
        "task": "signal_family_error_analysis",
        "dataset_path": _display_path(labels_path),
        "predictions_path": _display_path(predictions_path),
        "dataset_size": len(labels_by_id),
        "evaluation_scope": metrics.get("split_strategy"),
        "split_details": metrics.get("split_details", {}),
        "canonical_system": "deterministic_rules",
        "benchmark_context": {
            "warning": "Early labeled benchmark only, not statistical proof.",
            "benchmark_runs": metrics.get("benchmark_runs", []),
        },
        "error_buckets": {
            "counts": counts,
            "definitions": {
                "both_wrong": "Neither deterministic rules nor classifier matched the gold label.",
                "classifier_only_correct": "Classifier matched gold label and rules did not.",
                "rules_only_correct": "Rules matched gold label and classifier did not.",
                "ambiguous_or_low_confidence": "Low classifier confidence, weak rule evidence, or near-tie signal.",
            },
        },
        "grouped_summary": {key: dict(counter) for key, counter in grouped.items()},
        "recommended_action_summary": dict(action_counts),
        "cases": case_rows,
        "limitations": [
            "Small seeded dataset.",
            "Classifier variants are exploratory only.",
            "Deterministic rules remain canonical.",
        ],
    }

    write_json(json_out, payload)
    write_csv(
        csv_out,
        fieldnames=[
            "id",
            "domain",
            "source_file",
            "text",
            "text_length_bucket",
            "gold_label",
            "deterministic_label",
            "deterministic_correct",
            "deterministic_evidence_terms",
            "deterministic_evidence_count",
            "classifier_label",
            "classifier_correct",
            "classifier_confidence",
            "classifier_top2_labels",
            "classifier_margin",
            "error_bucket",
            "bucket_tags",
            "priority_score",
            "priority_reason",
            "recommended_actions",
            "label_source",
            "notes",
        ],
        rows=[
            {
                "id": row["id"],
                "domain": row["domain"],
                "source_file": row["source_file"],
                "text": row["text"],
                "text_length_bucket": row["text_length_bucket"],
                "gold_label": row["gold_label"],
                "deterministic_label": row["deterministic_label"],
                "deterministic_correct": row["deterministic_correct"],
                "deterministic_evidence_terms": "|".join(row["deterministic_evidence_terms"]),
                "deterministic_evidence_count": row["deterministic_evidence_count"],
                "classifier_label": row["classifier_label"],
                "classifier_correct": row["classifier_correct"],
                "classifier_confidence": row["classifier_confidence"],
                "classifier_top2_labels": "|".join(row["classifier_top2_labels"]),
                "classifier_margin": row["classifier_margin"],
                "error_bucket": row["error_bucket"],
                "bucket_tags": "|".join(row["bucket_tags"]),
                "priority_score": row["priority_score"],
                "priority_reason": row["priority_reason"],
                "recommended_actions": "|".join(row["recommended_actions"]),
                "label_source": row["label_source"],
                "notes": row["notes"],
            }
            for row in sorted(case_rows, key=lambda item: (-item["priority_score"], item["id"]))
        ],
    )
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(_render_report(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "case_count": len(case_rows), "json_out": str(json_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
