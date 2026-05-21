from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .schema import REVIEW_QUEUE_FIELDS, json_schema


def write_outputs(out_dir: Path, rows: list[dict[str, str]], validation_issues: list[dict[str, str]], *, include_csv: bool, include_jsonl: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if include_csv:
        write_csv(out_dir / "review_queue.csv", rows, REVIEW_QUEUE_FIELDS)
    if include_jsonl:
        write_jsonl(out_dir / "review_queue.jsonl", rows)
    write_csv(out_dir / "summary_by_case_label.csv", summary_by_case_label(rows), SUMMARY_CASE_FIELDS)
    write_csv(out_dir / "summary_by_priority.csv", summary_by_priority(rows), SUMMARY_PRIORITY_FIELDS)
    (out_dir / "review_packet_sample.md").write_text(render_review_packet_sample(rows), encoding="utf-8")
    (out_dir / "README_gold_review_workbench.md").write_text(render_readme(rows), encoding="utf-8")
    (out_dir / "reviewer_instructions.md").write_text(render_reviewer_instructions(), encoding="utf-8")
    (out_dir / "review_queue.schema.json").write_text(json.dumps(json_schema(), indent=2) + "\n", encoding="utf-8")
    write_validation_report(out_dir / "validation_report.json", rows, validation_issues)
    write_prompt_pack(out_dir / "prompt_pack")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps({field: row.get(field, "") for field in REVIEW_QUEUE_FIELDS}, ensure_ascii=False, sort_keys=True) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


SUMMARY_CASE_FIELDS = (
    "case_id",
    "suggested_label",
    "total_candidates",
    "high_priority_count",
    "medium_priority_count",
    "low_priority_count",
    "unmatched_context_count",
    "likely_boilerplate_count",
)

SUMMARY_PRIORITY_FIELDS = (
    "likely_review_priority",
    "suggested_label",
    "total_candidates",
    "unique_cases",
    "unmatched_context_count",
    "likely_boilerplate_count",
)


def summary_by_case_label(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("case_id", ""), row.get("suggested_label", ""))].append(row)
    output: list[dict[str, Any]] = []
    for (case_id, label), items in sorted(grouped.items()):
        priorities = Counter(row.get("likely_review_priority", "") for row in items)
        output.append(
            {
                "case_id": case_id,
                "suggested_label": label,
                "total_candidates": len(items),
                "high_priority_count": priorities.get("HIGH", 0),
                "medium_priority_count": priorities.get("MEDIUM", 0),
                "low_priority_count": priorities.get("LOW", 0),
                "unmatched_context_count": unmatched_count(items),
                "likely_boilerplate_count": sum(1 for row in items if row.get("is_likely_boilerplate") == "yes"),
            }
        )
    return output


def summary_by_priority(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("likely_review_priority", ""), row.get("suggested_label", ""))].append(row)
    output: list[dict[str, Any]] = []
    for (priority, label), items in sorted(grouped.items()):
        output.append(
            {
                "likely_review_priority": priority,
                "suggested_label": label,
                "total_candidates": len(items),
                "unique_cases": len({row.get("case_id", "") for row in items if row.get("case_id", "")}),
                "unmatched_context_count": unmatched_count(items),
                "likely_boilerplate_count": sum(1 for row in items if row.get("is_likely_boilerplate") == "yes"),
            }
        )
    return output


def unmatched_count(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("evidence_match_status") not in {"exact_match", "normalized_whitespace_match", "fuzzy_match"})


def write_validation_report(path: Path, rows: list[dict[str, str]], validation_issues: list[dict[str, str]]) -> None:
    parser_warning_count = sum(1 for row in rows if row.get("parser_warning"))
    payload = {
        "row_count": len(rows),
        "parser_warning_count": parser_warning_count,
        "schema_issue_count": len(validation_issues),
        "strict_pass": parser_warning_count == 0 and not validation_issues,
        "validation_issues": validation_issues,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render_review_packet_sample(rows: list[dict[str, str]], limit: int = 12) -> str:
    lines = [
        "# Gold Review Packet Sample",
        "",
        "This sample is for human adjudication only. Machine-surfaced suggestions are not gold labels.",
        "",
    ]
    for row in rows[:limit]:
        lines.extend(
            [
                f"## {row.get('candidate_id', '')}",
                "",
                f"- case_id: `{row.get('case_id', '')}`",
                f"- suggested_label: `{row.get('suggested_label', '')}`",
                f"- suggested_confidence: `{row.get('suggested_confidence', '')}`",
                f"- priority: `{row.get('likely_review_priority', '')}`",
                f"- priority_reason: {row.get('priority_reason', '')}",
                f"- source_file: `{row.get('source_file', '')}`",
                f"- transcript_file_if_matched: `{row.get('transcript_file_if_matched', '')}`",
                "",
                "```text",
                row.get("evidence_span", ""),
                "```",
                "",
                "Human decision: accept / reject / relabel / unsure",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_readme(rows: list[dict[str, str]]) -> str:
    priorities = Counter(row.get("likely_review_priority", "") for row in rows)
    return "\n".join(
        [
            "# Gold Review Workbench",
            "",
            "This directory contains a human adjudication queue for Signal Engine earnings-call labels.",
            "",
            "This creates a human adjudication queue. It does not create gold labels automatically.",
            "It does not claim statistical significance. It does not provide trading advice.",
            "Later promotion requires separate human-reviewed acceptance through the project's gold-label workflow.",
            "",
            "## Contents",
            "",
            "- `review_queue.csv`: spreadsheet-friendly adjudication queue.",
            "- `review_queue.jsonl`: machine-readable copy of the same queue.",
            "- `summary_by_case_label.csv`: counts by case and suggested label.",
            "- `summary_by_priority.csv`: counts by deterministic review priority.",
            "- `review_packet_sample.md`: small markdown sample for reviewers.",
            "- `reviewer_instructions.md`: human review rules.",
            "- `prompt_pack/`: reusable Deep Research, Agent, and Codex prompts.",
            "",
            "## How To Review",
            "",
            "Open `review_queue.csv`, read `evidence_span` and `surrounding_context`, then fill only the blank adjudication columns.",
            "Accepted rows must include `final_evidence_span`. If the transcript does not explicitly support the label, reject or mark unsure.",
            "",
            "## Generated Summary",
            "",
            f"- total_candidates: `{len(rows)}`",
            f"- high_priority: `{priorities.get('HIGH', 0)}`",
            f"- medium_priority: `{priorities.get('MEDIUM', 0)}`",
            f"- low_priority: `{priorities.get('LOW', 0)}`",
            "",
            "## What This Does Not Do",
            "",
            "- It does not promote weak labels or machine candidates to gold.",
            "- It does not overwrite canonical gold labels.",
            "- It does not make alpha, stock-movement, or execution recommendations.",
            "- It does not make precision, recall, F1, uplift, or statistical-significance claims.",
            "",
        ]
    )


def render_reviewer_instructions() -> str:
    return "\n".join(
        [
            "# Reviewer Instructions",
            "",
            "- Do not predict stock movement.",
            "- Decide whether the highlighted transcript span supports the proposed signal label.",
            "- Only accept labels supported explicitly by the transcript.",
            "- Do not infer management intent beyond the text.",
            "- If unsure, mark `unsure`.",
            "- Every accepted label must include `final_evidence_span`.",
            "- Suggested decisions: `accept`, `reject`, `relabel`, `unsure`.",
            "- Suggested labels: `opportunity_commitment`, `risk_friction`, `uncertainty_hedging`, `neutral`, `other`.",
            "- Time yourself in seconds and enter the result in `time_spent_seconds`.",
            "",
        ]
    )


def write_prompt_pack(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "deep_research_prompt.md").write_text(DEEP_RESEARCH_PROMPT, encoding="utf-8")
    (path / "agent_prompt.md").write_text(AGENT_PROMPT, encoding="utf-8")
    (path / "codex_prompt.md").write_text(CODEX_PROMPT, encoding="utf-8")


DEEP_RESEARCH_PROMPT = """# Deep Research Prompt: Earnings-Call Signal Extraction Evaluation

Prepare a cited research memo on evaluating transcript-first earnings-call signal extraction for a retail-facing review tool.

Cover guidance revision extraction, tone shift detection, analyst-management friction, uncertainty and reassurance language, evidence citation quality, retail baseline comparison, gold-label review design, inter-rater agreement, false-positive risks, and what must remain human-adjudicated.

Respect these boundaries: do not make trading recommendations, do not claim statistical significance without sufficient evidence, and do not treat machine-surfaced candidates as gold labels. Explain how evidence spans and transcript provenance should remain canonical.
"""

AGENT_PROMPT = """# ChatGPT Agent Prompt: Build A Human Gold Review Queue

Using the uploaded labeling packets, weak-label files, transcripts, and project docs, create a structured human review queue.

Return `review_queue.csv`, `review_queue.jsonl`, summary tables by case/label and priority, and blank adjudication columns. Preserve exact evidence spans, source paths, candidate IDs, and transcript context windows. Include a review-priority summary.

Do not promote machine labels to gold. Do not infer labels beyond the transcript. Do not fill human adjudication fields. Do not make trading, alpha, or statistical-significance claims.
"""

CODEX_PROMPT = """# Codex Rerun Prompt

Run the Signal Engine Gold Review Workbench from the repo root:

```bash
python -m signal_engine.review_queue.build \\
  --packets 'data/corpus/high_signal_cases/*/labels/human_labeling_packet.md' \\
  --transcripts data/corpus/high_signal_cases \\
  --out artifacts/gold_review \\
  --verbose
```

Verify that the output is a human adjudication queue only, with blank review fields, preserved provenance, transcript context, summaries, prompt pack, and no automatic gold-label promotion.
"""
