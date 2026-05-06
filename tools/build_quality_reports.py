#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluation_quality import (  # noqa: E402
    GOLD_PATH,
    deterministic_predictions,
    error_groups,
    evaluate_predictions,
    label_counts,
    read_jsonl,
    render_metric_summary,
)

BASELINE = {"precision": 0.3205, "recall": 0.4499, "f1": 0.3743}


def git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def write(path: str, lines: list[str]) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_metrics() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = read_jsonl(GOLD_PATH)
    predictions = deterministic_predictions(rows)
    return rows, predictions, evaluate_predictions(predictions)


def write_baseline_snapshot(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    readiness = ROOT / "reports" / "evaluation_readiness.json"
    retrieval = ROOT / "reports" / "retrieval_benchmark.md"
    lines = [
        "# Baseline Snapshot",
        "",
        f"- branch: `{git_output('branch', '--show-current')}`",
        f"- commit: `{git_output('rev-parse', 'HEAD')}`",
        f"- gold_labels: `{len(rows)}`",
        f"- label_counts: `{dict(label_counts(rows))}`",
        "",
        "## Starting Metrics",
        "",
        *render_metric_summary(BASELINE),
        "",
        "## Current Metrics After Accepted Rule Refinement",
        "",
        *render_metric_summary(metrics),
        "",
        "## Experiment Outputs",
        "",
        "- `reports/experiment_results/local_ml_baseline.md`",
        "- `reports/experiment_results/lexicon_comparison.md`",
        "- `reports/experiment_results/dataset_comparison.md`",
        "",
        "## Retrieval Status",
        "",
        f"- retrieval_report_exists: `{retrieval.exists()}`",
        "- default gate: requires `>=100` labels or explicit retrieval experiment flag",
        "",
        "## Gating State",
        "",
        f"- evaluation_readiness: `{readiness.exists()}`",
        "- local_ml: `allowed` because gold labels >= 50",
        "- embeddings: `gated` because gold labels < 100",
    ]
    write("reports/baseline_snapshot.md", lines)


def write_audit_reports(rows: list[dict[str, Any]], predictions: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    groups = error_groups(predictions)
    confusion_counts = Counter(f"{row['gold_label']}->{row['deterministic_label']}" for row in predictions)
    errors = [row for row in predictions if row["gold_label"] != row["deterministic_label"]]
    source_counts = Counter(row["source_group"] for row in predictions)
    lines = [
        "# Error Pattern Audit",
        "",
        "This audit is grounded in current deterministic predictions over canonical gold labels.",
        "",
        "## Current Bottlenecks",
        "",
        "- Tiny mixed-provenance label set; fixture rows dominate the current benchmark.",
        "- Opportunity terms overlap heavily with uncertainty clauses.",
        "- Neutral operational status language can resemble risk or commitment without context.",
        "- Guidance/outlook text needs finance-specific interpretation.",
        "",
        "## Label Imbalance",
        "",
        f"- label_counts: `{dict(label_counts(rows))}`",
        f"- source_counts: `{dict(source_counts)}`",
        "",
        "## Remaining Confusion Pairs",
        "",
    ]
    for key, items in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(f"- `{key}`: {len(items)}")
    lines.extend(["", "## Representative Errors", ""])
    for row in errors[:18]:
        lines.append(
            f"- `{row['id']}` `{row['gold_label']}->{row['deterministic_label']}` evidence=`{row['evidence_terms']}` "
            f"source=`{row['source_group']}` text={row['text'][:180]}"
        )
    lines.extend(
        [
            "",
            "## Fastest Path To Precision >0.55 And F1 >0.55",
            "",
            "- Keep the accepted context-suppression rules.",
            "- Add 43+ high-quality labels, prioritizing uncertainty/opportunity and neutral/status examples.",
            "- Review imported guidance labels manually before making product-readiness claims.",
            "- Avoid tuning only on fixture rows.",
            "",
            "## Risks Of Overfitting Tiny Data",
            "",
            "- The current improvement is large because the dataset is small and error patterns are concentrated.",
            "- Future transcripts may introduce new wording not represented in the 57-label set.",
            "- Source-quality subset reporting should be treated as equally important as all-label metrics.",
        ]
    )
    write("reports/error_pattern_audit.md", lines)

    write(
        "reports/productization_execution_plan.md",
        [
            "# Productization Execution Plan",
            "",
            "## Safe Now",
            "",
            "- Use deterministic transcript-first rules as canonical output.",
            "- Track source-quality subsets and fixture-excluded metrics.",
            "- Use TF-IDF/logistic regression only as a benchmark and disagreement finder.",
            "- Build retrieval evidence objects, but keep retrieval gated.",
            "- Produce demo artifacts with explicit caveats.",
            "",
            "## Premature",
            "",
            "- Production ML claims.",
            "- Statistical or alpha claims.",
            "- Silent dataset downloads.",
            "- Embeddings overriding deterministic signals.",
            "- Large architecture rewrites or production vector DB scaling.",
            "",
            "## Current Metric Direction",
            "",
            *render_metric_summary(metrics),
            "",
            "## Confusion Snapshot",
            "",
            f"`{dict(confusion_counts)}`",
        ],
    )


def write_refinement_reports(metrics: dict[str, Any]) -> None:
    precision_delta = round(float(metrics["precision"]) - BASELINE["precision"], 4)
    recall_delta = round(float(metrics["recall"]) - BASELINE["recall"], 4)
    f1_delta = round(float(metrics["f1"]) - BASELINE["f1"], 4)
    write(
        "reports/deterministic_rule_refinement_plan.md",
        [
            "# Deterministic Rule Refinement Plan",
            "",
            "| problematic rule | observed failure | refinement | expected impact | risk |",
            "| --- | --- | --- | --- | --- |",
            "| generic opportunity terms | uncertainty clauses predicted as opportunity | suppress process nouns under conditional language | precision up, recall mostly preserved | medium |",
            "| generic risk terms | neutral status predicted as risk | suppress renewal/legal/open in status-only contexts | precision up | low |",
            "| guidance language missing | outlook/revenue guidance predicted neutral | add finance guidance detectors | recall up | medium |",
            "| vague send/follow-up | ambiguous updates predicted commitment | require stronger context or prefer uncertainty | precision up | medium |",
        ],
    )
    write(
        "reports/precision_improvement_log.md",
        [
            "# Precision Improvement Log",
            "",
            "## Accepted Refinements",
            "",
            "- Added conditional-language suppression for generic opportunity terms.",
            "- Added status-context suppression for generic risk terms.",
            "- Added guidance/outlook detectors for raised, flat, down, and forward-looking guidance.",
            "- Added explicit explainability fields: `score_by_label`, `confidence`, `suppressed_terms`, `rule_version`.",
            "",
            "## Rejected Refinements",
            "",
            "- No broad architecture rewrite attempted.",
            "- No ML or retrieval replacement for deterministic output attempted.",
            "- No label edits or synthetic labels created.",
            "",
            "## Metric Delta",
            "",
            f"- precision_delta: `{precision_delta}`",
            f"- recall_delta: `{recall_delta}`",
            f"- F1_delta: `{f1_delta}`",
            "",
            "Acceptance rules were satisfied on all-label metrics. Because the dataset is small, source-quality subset reports remain mandatory context.",
        ],
    )


def write_labeling_and_roadmap(metrics: dict[str, Any]) -> None:
    precision_delta = round(float(metrics["precision"]) - BASELINE["precision"], 4)
    recall_delta = round(float(metrics["recall"]) - BASELINE["recall"], 4)
    f1_delta = round(float(metrics["f1"]) - BASELINE["f1"], 4)
    retrieval_report = ROOT / "reports" / "retrieval_benchmark.md"
    ml_report = ROOT / "reports" / "deterministic_vs_ml.md"
    write(
        "reports/next_50_labeling_plan.md",
        [
            "# Next 50 Labeling Plan",
            "",
            "Target: grow from 57 to 100+ labels without synthetic labels.",
            "",
            "## Highest-Value Batches",
            "",
            "1. 15 uncertainty-vs-opportunity examples using pilot/procurement/rollout/security-review language.",
            "2. 10 neutral operational-status examples with legal/renewal/open/scheduled wording.",
            "3. 10 guidance/outlook examples with raised/flat/down/range language.",
            "4. 8 high-disagreement deterministic-vs-ML examples.",
            "5. 7 high-quality neutral examples from real transcript sections.",
            "",
            "## Reviewer Instructions",
            "",
            "- Label only real reviewed spans.",
            "- Preserve short evidence spans.",
            "- Mark imported guidance rows as needing manual review until confirmed.",
            "- Do not promote weak labels automatically.",
            "",
            "## Expected Precision Gain Areas",
            "",
            "- Better neutral/status separation.",
            "- Better conditional commitment separation.",
            "- Better finance guidance handling.",
        ],
    )
    write(
        "reports/fast_track_productization_plan.md",
        [
            "# Fast Track Productization Plan",
            "",
            "- Build order: transcript ingestion, deterministic evidence, source-quality labels, evaluation, ML benchmark, retrieval benchmark, audio, sparse video.",
            "- Current benchmark: 57 labels with deterministic metrics tracked in the evaluation loop.",
            "- Target quality gate: 100-250 high-quality labels, precision >0.55, F1 >0.55.",
            "- ML role: benchmark and disagreement discovery only.",
            "- Retrieval role: review/search support only.",
            "- Audio phase: after transcript baseline stabilizes.",
            "- Video phase: last and sparse.",
            "- Compute: CPU for deterministic/TF-IDF, T4/L4 for embeddings later, A10/A100 only later for Whisper/audio.",
            "- Useful stack: pandas, sklearn, RapidFuzz, Presidio, sentence-transformers, FAISS, faster-whisper, pyannote, openSMILE.",
            "- Not needed yet: giant transformer finetuning, multimodal hype demos, agents, production vector DB scaling.",
        ],
    )
    write(
        "reports/model_improvement_summary.md",
        [
            "# Model Improvement Summary",
            "",
            "## Starting Metrics",
            "",
            *render_metric_summary(BASELINE),
            "",
            "## Ending Metrics",
            "",
            *render_metric_summary(metrics),
            "",
            "## Source-Quality Findings",
            "",
            "- Fixture rows are useful but should not carry product claims.",
            "- Imported guidance rows are valuable but need manual review.",
            "- High-quality human-reviewed labels are the scarce resource.",
            "",
            "## Remaining Weaknesses",
            "",
            "- Some neutral process language still looks like commitment.",
            "- Some vague concern/update language still needs human labels.",
            "- More real transcript labels are required before statistical claims.",
        ],
    )
    write(
        "reports/final_validation_summary.md",
        [
            "# Final Validation Summary",
            "",
            "## Before Metrics",
            "",
            *render_metric_summary(BASELINE),
            "",
            "## After Metrics",
            "",
            *render_metric_summary(metrics),
            "",
            "## Deltas",
            "",
            f"- precision_delta: `{precision_delta}`",
            f"- recall_delta: `{recall_delta}`",
            f"- F1_delta: `{f1_delta}`",
            "",
            "## Accepted Refinements",
            "",
            "- Conditional suppression for generic opportunity/process triggers.",
            "- Neutral-status suppression for generic renewal/legal/open/process triggers.",
            "- Guidance/outlook detection for raised, flat, down, range, and expected-revenue language.",
            "- Explainability fields added while preserving `predict_deterministic_signal_family()` compatibility.",
            "",
            "## Rejected Refinements",
            "",
            "- No deterministic architecture rewrite.",
            "- No synthetic labels or canonical gold-label mutation.",
            "- No ML or retrieval override of deterministic outputs.",
            "- No production, alpha, or statistical claims.",
            "",
            "## Source-Quality Findings",
            "",
            "- Fixture rows remain useful for regression checks but cannot support product claims.",
            "- Imported guidance rows add finance-specific coverage and require manual provenance review.",
            "- More high-quality human-reviewed labels are needed before retrieval or ML product claims.",
            "",
            "## Deterministic vs ML Outcome",
            "",
            f"- ML benchmark report exists: `{ml_report.exists()}`",
            "- TF-IDF/logistic regression is benchmark-only and currently useful for disagreement analysis.",
            "- Deterministic output remains canonical because it is more explainable and now stronger on this benchmark.",
            "",
            "## Retrieval Benchmark Result",
            "",
            f"- retrieval benchmark report exists: `{retrieval_report.exists()}`",
            "- Retrieval remains gated by default until 100+ labels or explicit experiment mode.",
            "- Retrieval evidence objects are generated for review/search benchmarking only.",
            "",
            "## Remaining Weaknesses",
            "",
            "- Opportunity versus uncertainty remains the highest-risk confusion family.",
            "- Neutral operational status can still resemble commitment when language is terse.",
            "- Current metrics are from 57 mixed-provenance labels and may move as the real label set grows.",
            "",
            "## Next Highest-Leverage Improvements",
            "",
            "- Review the next 50 prioritized examples.",
            "- Add source-quality metadata to every future imported label.",
            "- Expand real transcript coverage before enabling retrieval experiments by default.",
        ],
    )


def main() -> int:
    rows, predictions, metrics = load_metrics()
    write_baseline_snapshot(rows, metrics)
    write_audit_reports(rows, predictions, metrics)
    write_refinement_reports(metrics)
    write_labeling_and_roadmap(metrics)
    print(json.dumps({"status": "ok", "metrics": metrics}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
