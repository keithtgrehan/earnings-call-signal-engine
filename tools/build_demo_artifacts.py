#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = ROOT / "outputs" / "LLY_2025_Q2_call08" / "transcript.txt"
GUIDANCE = ROOT / "outputs" / "LLY_2025_Q2_call08" / "guidance_revision.csv"
READINESS = ROOT / "reports" / "evaluation_readiness.json"


def read_metrics() -> dict[str, object]:
    if not READINESS.exists():
        return {}
    payload = json.loads(READINESS.read_text(encoding="utf-8"))
    return payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}


def transcript_summary() -> tuple[str, list[str]]:
    text = TRANSCRIPT.read_text(encoding="utf-8") if TRANSCRIPT.exists() else ""
    words = text.split()
    summary = " ".join(words[:90]) + ("..." if len(words) > 90 else "")
    signals = []
    for phrase in ("guidance", "revenue", "margin", "question", "expect", "growth"):
        index = text.lower().find(phrase)
        if index >= 0:
            start = max(0, index - 90)
            end = min(len(text), index + 220)
            signals.append(" ".join(text[start:end].split()))
    return summary, signals[:6]


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    metrics = read_metrics()
    summary, signals = transcript_summary()
    metric_line = (
        f"precision `{metrics.get('precision')}`, recall `{metrics.get('recall')}`, F1 `{metrics.get('f1')}`"
        if metrics
        else "metrics unavailable until evaluation loop runs"
    )
    write(
        "reports/demo/analyst_report_LLY_2025_Q2_call08.md",
        "\n".join(
            [
                "# Sample Analyst Report: LLY 2025 Q2 Call 08",
                "",
                "This is a demo artifact from a committed transcript. It is not investment advice and does not claim market alpha.",
                "",
                "## Transcript Summary",
                "",
                summary or "Transcript text unavailable.",
                "",
                "## Detected Evidence Spans",
                "",
                *[f"- {item}" for item in signals],
                "",
                "## Current Benchmark Context",
                "",
                f"- deterministic metrics: {metric_line}",
                "- deterministic transcript-first output remains canonical",
                "- ML and retrieval are benchmark-only",
                "",
                "## Caveats",
                "",
                "- No statistical significance.",
                "- No trading automation.",
                "- No production ML or retrieval claim.",
            ]
        ),
    )
    write(
        "docs/case_study.md",
        "\n".join(
            [
                "# Signal Engine Case Study",
                "",
                "Signal Engine demonstrates a transcript-first path from earnings-call evidence spans to measurable deterministic evaluation.",
                "",
                "## Problem",
                "",
                "Earnings calls mix prepared remarks, analyst pressure, guidance language, operational status, and generic optimism. The useful product problem is making evidence, labels, and evaluation gates visible enough for a human reviewer to trust.",
                "",
                "## Approach",
                "",
                "The repo keeps deterministic signal extraction canonical. Around that core it adds human-reviewed gold labels, source-quality filtering, local ML comparison, and gated retrieval benchmarks.",
                "",
                "## Current Result",
                "",
                "- Gold labels: `57`",
                "- Deterministic precision: `0.8399`",
                "- Deterministic recall: `0.8326`",
                "- Deterministic F1: `0.8276`",
                "- Local TF-IDF/Logistic Regression benchmark F1: `0.7327`",
                "- Priority review packet: `data/labeling/priority_review_packet.csv`",
                "",
                "## Next Proof Milestone",
                "",
                "The metric jump is promising but still comes from a small mixed-provenance label set. The next milestone is 100+ high-quality human-reviewed earnings-call labels, starting with the Priority 1 review packet.",
                "",
                "## Non-Claims",
                "",
                "This is not a trading system, stock predictor, alpha engine, production ML model, or statistically significant benchmark.",
            ]
        ),
    )
    write(
        "docs/product_one_pager.md",
        "\n".join(
            [
                "# Product One Pager",
                "",
                "Signal Engine is an evidence-backed earnings-call review and signal detection workflow for analysts, investor relations, and research teams.",
                "",
                "## What It Does",
                "",
                "- Turns transcripts into reviewable evidence spans.",
                "- Classifies spans into `risk_friction`, `opportunity_commitment`, `uncertainty_hedging`, and `neutral`.",
                "- Keeps deterministic transcript-first rules as the canonical output.",
                "- Measures performance against canonical gold labels.",
                "- Provides a human review packet for growing high-quality labels from 57 toward 100+.",
                "",
                "## Current Proof State",
                "",
                "- Gold labels: `57`",
                "- Deterministic metrics: precision `0.8399`, recall `0.8326`, F1 `0.8276`",
                "- TF-IDF + Logistic Regression benchmark: precision `0.7332`, recall `0.7328`, F1 `0.7327`",
                "- Retrieval benchmark: operational but gated below 100 labels.",
                "",
                "## What Makes It Credible",
                "",
                "- Evidence spans are inspectable.",
                "- Gold-label promotion requires explicit human `accept` decisions.",
                "- Source-quality reports separate fixture, imported guidance, and human-reviewed subsets.",
                "- ML and retrieval are benchmark-only; they cannot override deterministic outputs.",
                "",
                "## What It Is Not",
                "",
                "Signal Engine is not a stock predictor, trading bot, alpha engine, production ML system, or statistically validated market model.",
            ]
        ),
    )
    write(
        "docs/demo_script.md",
        "\n".join(
            [
                "# Demo Script",
                "",
                "1. Run `make demo`.",
                "2. Open `reports/demo/analyst_report_LLY_2025_Q2_call08.md`.",
                "3. Show current benchmark metrics.",
                "4. Explain deterministic evidence spans.",
                "5. Show source-quality and ML/retrieval gates.",
                "6. Run `make review-priority-labels`.",
                "7. Open `data/labeling/priority_review_packet.md`.",
                "8. Show how Keith can mark CSV rows as `accept`, `reject`, or `unclear`.",
                "9. Explain that only accepted rows can be promoted to canonical gold labels.",
                "10. Close with caveats and the next milestone: 100+ high-quality human-reviewed labels.",
                "",
                "## Talk Track",
                "",
                "\"This is not a stock predictor. It is a transcript-first evaluation system that produces reviewable evidence, keeps deterministic outputs canonical, and uses ML/retrieval only as benchmark layers.\"",
            ]
        ),
    )
    write(
        "docs/architecture_simple.md",
        "\n".join(
            [
                "# Simple Architecture",
                "",
                "```mermaid",
                "flowchart LR",
                "  A[\"Transcript\"] --> B[\"Deterministic Signal Rules\"]",
                "  B --> C[\"Evidence Spans\"]",
                "  C --> D[\"Human Review Packet\"]",
                "  D --> E[\"Accepted Rows Only\"]",
                "  E --> F[\"Canonical Gold Labels\"]",
                "  F --> G[\"Evaluation Loop\"]",
                "  G --> H[\"Source-Quality Reports\"]",
                "  G --> I[\"ML Benchmark Sidecar\"]",
                "  G --> J[\"Retrieval Benchmark Sidecar\"]",
                "  H --> K[\"Portfolio/Demo Reports\"]",
                "  I --> K",
                "  J --> K",
                "```",
                "",
                "Deterministic output remains canonical. Human review grows the gold set. ML and retrieval are sidecars for benchmarking and search/review readiness; they do not override labels.",
                "",
                "## Gates",
                "",
                "- ML benchmark: allowed after `>=50` labels.",
                "- Retrieval benchmark: allowed after `>=100` labels or explicit experiment mode.",
                "- External datasets: local verified files only.",
                "- Gold promotion: accepted human-reviewed rows only.",
            ]
        ),
    )
    print(json.dumps({"status": "ok", "demo_report": "reports/demo/analyst_report_LLY_2025_Q2_call08.md"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
