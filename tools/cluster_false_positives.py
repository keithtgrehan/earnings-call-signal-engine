#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluation_quality import GOLD_PATH, deterministic_predictions, phrase_hits, read_jsonl, tokens  # noqa: E402

CLUSTERS = {
    "hedge_or_conditional": {"if", "whether", "probably", "maybe", "may", "might", "could", "depends", "once"},
    "rollout_procurement_pilot": {"rollout", "procurement", "pilot", "security review", "implementation", "expansion"},
    "generic_positive_or_commitment": {"send", "follow up", "schedule", "review", "owner", "fixed", "recovery plan"},
    "weak_blocker_language": {"legal", "renewal", "still open", "discount", "pricing", "someone will reach out"},
    "guidance_outlook": {"guidance", "outlook", "expect", "expected", "revenue", "plus or minus"},
}


def cluster_errors(predictions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        if row["gold_label"] == row["deterministic_label"]:
            continue
        text = row["text"].lower()
        assigned = False
        for name, phrases in CLUSTERS.items():
            hits = phrase_hits(text, phrases)
            if hits or any(term in row.get("evidence_terms", []) for term in phrases):
                clusters[name].append({**row, "cluster_hits": hits or row.get("evidence_terms", [])})
                assigned = True
        if not assigned:
            clusters["low_evidence_or_other"].append({**row, "cluster_hits": row.get("evidence_terms", [])})
    return dict(clusters)


def likely_root_cause(name: str) -> str:
    return {
        "hedge_or_conditional": "Conditional language is competing with commercial next-step vocabulary.",
        "rollout_procurement_pilot": "Lifecycle/process nouns are useful weak triggers but are not commitments by themselves.",
        "generic_positive_or_commitment": "Generic action verbs such as send/review need stronger evidence-span requirements.",
        "weak_blocker_language": "Operational status terms can describe neutral process state rather than risk.",
        "guidance_outlook": "Finance guidance language needs domain-specific rules rather than generic business terms.",
        "low_evidence_or_other": "The deterministic rule either had no evidence term or a sparse ambiguous span.",
    }.get(name, "Unknown root cause.")


def recommendation(name: str) -> str:
    return {
        "hedge_or_conditional": "Prefer uncertainty unless explicit owner/action commitment is present.",
        "rollout_procurement_pilot": "Suppress generic process terms under conditional or status-only contexts.",
        "generic_positive_or_commitment": "Require actor plus action plus deadline or concrete resolution.",
        "weak_blocker_language": "Require stronger risk terms before predicting risk_friction.",
        "guidance_outlook": "Use guidance-specific detectors for raised/flat/down/outlook statements.",
        "low_evidence_or_other": "Send examples to manual review and strengthen evidence extraction.",
    }.get(name, "Review examples manually.")


def write_report(clusters: dict[str, list[dict[str, Any]]]) -> None:
    lines = ["# False Positive Clusters", "", "Generated from current deterministic predictions over canonical gold labels.", ""]
    for name, rows in sorted(clusters.items(), key=lambda item: (-len(item[1]), item[0])):
        trigger_counts = Counter(hit for row in rows for hit in row.get("cluster_hits", []))
        affected = Counter(f"{row['gold_label']}->{row['deterministic_label']}" for row in rows)
        lines.extend(
            [
                f"## {name}",
                "",
                f"- examples: `{len(rows)}`",
                f"- confidence: `{'high' if len(rows) >= 3 else 'medium'}`",
                f"- likely_root_cause: {likely_root_cause(name)}",
                f"- recommended_refinement: {recommendation(name)}",
                f"- affected_labels: `{dict(affected)}`",
                f"- trigger_frequency: `{dict(trigger_counts.most_common(8))}`",
                "",
                "| id | confusion | triggers | text |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in rows[:8]:
            text = " ".join(tokens(row["text"])[:28])
            lines.append(
                f"| `{row['id']}` | `{row['gold_label']}->{row['deterministic_label']}` | "
                f"`{', '.join(map(str, row.get('cluster_hits', [])))}` | {text} |"
            )
        lines.append("")
    (ROOT / "reports" / "false_positive_clusters.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    predictions = deterministic_predictions(read_jsonl(GOLD_PATH))
    clusters = cluster_errors(predictions)
    write_report(clusters)
    print(json.dumps({"status": "ok", "clusters": {key: len(value) for key, value in clusters.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
