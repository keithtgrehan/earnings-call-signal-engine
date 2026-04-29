# Manual Corpus Case: META_2025_Q4

This folder is a manual intake scaffold only. It does not contain downloaded transcript text.

## Source Confirmation

- Company: `Meta Platforms Inc.`
- Ticker: `META`
- Fiscal period: `FY2025 Q4`
- Call date: `2026-01-28`
- Confirmed IR source: `https://investor.atmeta.com/investor-events/event-details/2026/Q4-2025-Earnings-Call/default.aspx`
- License/use status: `unknown`
- Current promotion status: `source-confirmed`

## Manual Transcript Acquisition

1. Manually review the confirmed IR page and any linked official event materials.
2. Confirm whether transcript reuse is allowed for local research.
3. Do not scrape transcript vendors or paid sources.
4. If a legally safe transcript is obtained, place it locally at `data/corpus/manual_cases/META_2025_Q4/raw/transcript.txt`.
5. Do not commit raw transcript text unless explicitly approved.

## File Path Conventions

- Raw transcript placeholder: `raw/transcript.txt`
- Sectioned output placeholder: `processed/sectioned_transcript.json`
- Manual labels placeholder: `labels/manual_labels.jsonl`
- Review report placeholder: `reports/review_report.md`

## Sectioning Rules

- Mark prepared remarks separately from Q&A.
- Preserve speaker turns in original order.
- Keep safe-harbor/operator language distinct from management commentary.
- Mark section as `unknown` when the boundary is not clear.

## Speaker Validation Rules

- Normalize management, analyst, and operator roles.
- Preserve original speaker names when available.
- Do not infer a role when the transcript does not support it.
- Flag ambiguous speakers for manual review.

## Labeling Expectations

- Use `data/gold_labels.example.jsonl` as the schema reference only.
- Add labels only after source, section, and speaker quality are checked.
- Prefer `unknown` direction over overclaiming.

## Evidence Span Requirements

- Evidence must be short, reviewable, and sufficient to justify the label.
- Evidence should include the topic and speaker context.
- Q&A friction evidence should include the analyst question and relevant management answer when possible.

## Promotion Pipeline

`source-confirmed -> transcript-ready -> sectioned -> labeled -> reviewed`
