# First 3 Corpus Intake Report

## Summary

Created the first small working slice of the 30-call corpus plan. This is source-confirmed intake metadata only. No transcript text, model output, audio, video, or paid/API content was downloaded or committed.

## Per-Case Status

| case_id | company | source status | license/use status | transcript status | blocker | next action |
|---|---|---|---|---|---|---|
| `NVDA_2026_Q4` | NVIDIA Corporation | `source-confirmed` | `unknown` | `missing` | Transcript reuse rights are not confirmed. | Manually confirm whether official IR materials or another lawful source permits local transcript use. |
| `META_2025_Q4` | Meta Platforms Inc. | `source-confirmed` | `unknown` | `missing` | Transcript reuse rights are not confirmed. | Manually confirm whether official IR materials or another lawful source permits local transcript use. |
| `AMZN_2025_Q4` | Amazon.com Inc. | `source-confirmed` | `unknown` | `missing` | Transcript reuse rights are not confirmed. | Manually confirm whether official IR materials or another lawful source permits local transcript use. |

## Confirmed Sources

| case_id | source_name | source_type | source_url |
|---|---|---|---|
| `NVDA_2026_Q4` | NVIDIA Investor Relations | `investor_relations` | `https://investor.nvidia.com/events-and-presentations/events-and-presentations/event-details/2026/NVIDIA-4th-Quarter-FY26-Financial-Results-2026-sO6kGS3C2P/default.aspx` |
| `META_2025_Q4` | Meta Investor Relations | `investor_relations` | `https://investor.atmeta.com/investor-events/event-details/2026/Q4-2025-Earnings-Call/default.aspx` |
| `AMZN_2025_Q4` | Amazon Investor Relations | `investor_relations` | `https://ir.aboutamazon.com/events/event-details/2026/Q4-2025-Amazoncom-Inc-Earnings-Conference-Call-/default.aspx` |

## Promotion Criteria

Promotion pipeline: `source-confirmed -> transcript-ready -> sectioned -> labeled -> reviewed`

- `source-confirmed`: official source URL recorded.
- `transcript-ready`: transcript reuse rights confirmed and permitted text is available locally.
- `sectioned`: prepared remarks, Q&A, operator/safe-harbor, and unknown sections are marked.
- `labeled`: reviewer-owned labels exist with valid evidence spans.
- `reviewed`: source, sectioning, speakers, labels, and evidence spans are checked.

## Files Added

- `data/corpus/manifests/first_30_working_manifest.csv`
- `data/corpus/manual_cases/NVDA_2026_Q4/`
- `data/corpus/manual_cases/META_2025_Q4/`
- `data/corpus/manual_cases/AMZN_2025_Q4/`
- `docs/first-3-corpus-intake-report.md`

## Validation

- `python scripts/validate_corpus_manifest.py --path data/corpus/manifests/first_30_working_manifest.csv`

Result: passed, 3 rows.

## What This Is Not

- Not a transcript corpus.
- Not validated training data.
- Not model work.
- Not evidence that transcript download rights have been cleared.
- Not a benchmark result or product validation claim.
