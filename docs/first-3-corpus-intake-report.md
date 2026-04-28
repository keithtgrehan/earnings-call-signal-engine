# First 3 Corpus Intake Report

## Summary

Created the first small working slice of the 30-call corpus plan. This is source-confirmed intake metadata only. No transcript text, model output, audio, video, or paid/API content was downloaded or committed.

## Cases Selected

| case_id | company | source_name | source_type | status | source_url |
|---|---|---|---|---|---|
| `NVDA_2026_Q4` | NVIDIA Corporation | NVIDIA Investor Relations | `investor_relations` | `source_confirmed` | `https://investor.nvidia.com/events-and-presentations/events-and-presentations/event-details/2026/NVIDIA-4th-Quarter-FY26-Financial-Results-2026-sO6kGS3C2P/default.aspx` |
| `META_2025_Q4` | Meta Platforms Inc. | Meta Investor Relations | `investor_relations` | `source_confirmed` | `https://investor.atmeta.com/investor-events/event-details/2026/Q4-2025-Earnings-Call/default.aspx` |
| `AMZN_2025_Q4` | Amazon.com Inc. | Amazon Investor Relations | `investor_relations` | `source_confirmed` | `https://ir.aboutamazon.com/events/event-details/2026/Q4-2025-Amazoncom-Inc-Earnings-Conference-Call-/default.aspx` |

## Files Added

- `data/corpus/manifests/first_30_working_manifest.csv`
- `data/corpus/manual_cases/NVDA_2026_Q4/README.md`
- `data/corpus/manual_cases/META_2025_Q4/README.md`
- `data/corpus/manual_cases/AMZN_2025_Q4/README.md`
- `.gitkeep` placeholders under each case `raw`, `processed`, `labels`, and `reports` folder
- `docs/first-3-corpus-intake-report.md`

## Validation

- `python scripts/validate_corpus_manifest.py --path data/corpus/manifests/first_30_working_manifest.csv`

Result: passed, 3 rows.

## What This Is

- A small manually selected intake manifest.
- A source-confirmed queue for future manual transcript handling.
- Empty per-case folder scaffolds with checklist READMEs and `.gitkeep` placeholders.

## What This Is Not

- Not a transcript corpus.
- Not validated training data.
- Not model work.
- Not evidence that transcript download rights have been cleared.
- Not a benchmark result or product validation claim.

## Next Manual Step

For each case, manually confirm transcript access rights and decide whether a legally safe local transcript can be used. If yes, place the text locally at the manifest `transcript_path`, keep raw text out of git unless explicitly approved, then begin section/speaker/evidence-span review.
