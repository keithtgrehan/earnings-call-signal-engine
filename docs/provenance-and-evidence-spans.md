# Provenance And Evidence Spans

Every evaluation output should be traceable back to a reviewed source and a specific transcript span. Provenance is what keeps deterministic scoring explainable.

## Required Provenance Fields

- Source file: local transcript or processed file used for extraction.
- Case ID: stable identifier such as `NVDA_2026_Q4`.
- Transcript section: prepared remarks, Q&A, or unknown.
- Speaker: normalized speaker name when available.
- Speaker role: management, analyst, operator, or unknown.
- Span ID: stable identifier for the extracted span or turn.
- Source URL: manually confirmed source pointer.
- Processing stage: placeholder, downloaded, parsed, sectioned, scored, labelled, or reviewed.
- Generated output path: path to prediction, report, or review artifact produced from the source.

## Evidence Span Rules

- Evidence must be short enough to review quickly.
- Evidence must preserve enough context to justify the signal.
- Evidence should not cross unrelated topics.
- Evidence should include the analyst question and management answer for Q&A friction when possible.
- Evidence offsets can be null in early examples, but reviewed corpora should add offsets or stable span IDs.

## Audit Trail

Promotion to a benchmark set should require a manifest row, a label row, source confirmation, and a reviewer note. If any piece is missing, the case should remain a candidate or be blocked.
