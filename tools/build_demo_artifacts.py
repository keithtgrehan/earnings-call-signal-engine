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
        "# Signal Engine Case Study\n\nSignal Engine demonstrates a transcript-first path from evidence spans to measurable deterministic evaluation. The current proof uses 57 canonical gold labels, source-quality filtering, deterministic metrics, and benchmark-only ML/retrieval layers.\n",
    )
    write(
        "docs/product_one_pager.md",
        "# Product One Pager\n\nSignal Engine is an explainable transcript intelligence layer for earnings-call review. It highlights candidate risk, opportunity, uncertainty, and neutral spans with evidence and evaluation gates. It is not a trading system and makes no alpha claims.\n",
    )
    write(
        "docs/demo_script.md",
        "# Demo Script\n\n1. Run `make demo`.\n2. Open `reports/demo/analyst_report_LLY_2025_Q2_call08.md`.\n3. Show current benchmark metrics.\n4. Explain deterministic evidence spans.\n5. Show source-quality and ML/retrieval gates.\n6. Close with caveats and next-labeling plan.\n",
    )
    write(
        "docs/architecture_simple.md",
        "# Simple Architecture\n\nTranscript -> deterministic signal rules -> gold-label evaluation -> source-quality filters -> ML benchmark sidecar -> retrieval benchmark sidecar -> portfolio reports.\n\nDeterministic output remains canonical. Sidecars do not override labels.\n",
    )
    print(json.dumps({"status": "ok", "demo_report": "reports/demo/analyst_report_LLY_2025_Q2_call08.md"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
