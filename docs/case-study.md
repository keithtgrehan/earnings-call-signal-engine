# Case Study: PVH Q1 2025

## Problem
Earnings calls hide the most important review moments inside long transcripts. A reviewer needs to know what changed, which moments deserve attention first, and where the supporting evidence lives.

## Why It Matters
`PVH_2025_Q1_call09` is the strongest portfolio-ready case in this repo because it combines:
- a fixed gold benchmark label
- a checked-in deterministic output bundle
- a review story that is easy to explain in under two minutes

The gold benchmark labels this case as `lowered`, making it a clear example of transcript-first evidence packaging rather than open-ended summarization.

## Approach
1. Start from the local transcript asset in [`data/gold_guidance_calls/raw_calls/PVH_2025_Q1_call09.txt`](../data/gold_guidance_calls/raw_calls/PVH_2025_Q1_call09.txt).
2. Score transcript segments and extract deterministic guidance, tone, and behavior artifacts.
3. Package the results into [`outputs/PVH_2025_Q1_call09/`](../outputs/PVH_2025_Q1_call09/).
4. Review the case through the report, metrics, guidance table, and supporting timeline image.

## Architecture
- Canonical input: transcript text
- Canonical outputs: deterministic files under [`outputs/PVH_2025_Q1_call09/`](../outputs/PVH_2025_Q1_call09/)
- Supporting only: audio behavior and multimodal support summaries
- Review surface: the local shell in [`app/`](../app/)

## Baseline vs Tool-Assisted
Baseline (manual review):
- A reader may miss lowered guidance wording if it is split across prepared remarks and Q&A.
- A reader may not consistently connect tariff headwinds, margin pressure, and analyst confidence questions.
- A reader may remember the narrative but lose the exact evidence span.

Tool-assisted:
- The system surfaces guidance-linked rows, including the operating-margin line marked as down versus last year.
- The system surfaces high uncertainty and high analyst skepticism in the checked-in scorecard.
- The system keeps report, metrics, and CSV artifacts together under one case directory.

## Example: Deterministic Extraction
Input:
"Overall, we are expecting our second quarter operating margin to be approximately 6.5 to 7%. Down, approximately 200 to 250 basis points compared to last year."

Output:
- metric: second-quarter operating margin
- prior value: last year baseline; exact value not extracted
- current value: approximately 6.5% to 7%
- direction: ↓
- evidence span: "Down, approximately 200 to 250 basis points compared to last year."

## Evidence Flow
1. Benchmark label: [`data/gold_guidance_calls/labels.csv`](../data/gold_guidance_calls/labels.csv) marks `call09` as `lowered`.
2. Review report: [`outputs/PVH_2025_Q1_call09/report.md`](../outputs/PVH_2025_Q1_call09/report.md) surfaces an amber overall review with high uncertainty and high analyst skepticism.
3. Structured scorecard: [`outputs/PVH_2025_Q1_call09/metrics.json`](../outputs/PVH_2025_Q1_call09/metrics.json) stores the machine-readable review summary.
4. Supporting files: [`guidance.csv`](../outputs/PVH_2025_Q1_call09/guidance.csv), [`analyst_skepticism.csv`](../outputs/PVH_2025_Q1_call09/analyst_skepticism.csv), [`qa_shift_summary.json`](../outputs/PVH_2025_Q1_call09/qa_shift_summary.json), and [`sentiment_timeline.png`](../outputs/PVH_2025_Q1_call09/sentiment_timeline.png).

## Example Outputs
- [`report.md`](../outputs/PVH_2025_Q1_call09/report.md): reviewer-facing summary with ranked categories and strongest evidence snippets
- [`metrics.json`](../outputs/PVH_2025_Q1_call09/metrics.json): structured scorecard payload for downstream use
- [`guidance.csv`](../outputs/PVH_2025_Q1_call09/guidance.csv): extracted guidance-linked rows
- [`sentiment_timeline.png`](../outputs/PVH_2025_Q1_call09/sentiment_timeline.png): simple visual artifact for presentation

![PVH deterministic timeline](../outputs/PVH_2025_Q1_call09/sentiment_timeline.png)

## Limitations
- This is a review workflow, not a prediction engine.
- The checked-in PVH bundle does not include a prior-guidance comparison input, so `guidance_revision.csv` is empty by design.
- Video support is unavailable for this case, and audio support remains additive only.
- The benchmark package is intentionally small and conservative.

## Why Deterministic-First
- Every major claim in the walkthrough can be traced to a file.
- The reviewer can inspect transcript-linked evidence instead of trusting an opaque summary.
- Optional narrative or multimodal layers never replace the canonical deterministic artifacts.
