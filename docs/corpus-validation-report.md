# Corpus Validation Report

## Run Context

- Branch: `codex/transcript-corpus-pipeline`
- Commit at review start: `30e926e68ff99f4b93464b88c175695ab964267a`
- Corpus root: `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts`
- Latest discovered backup path: `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts_backup_20260429_132004`

## Current Corpus Status

- Active case count: 31
- Audit status after heuristic cleanup: 16 pass, 15 warning, 0 fail
- Quarantined cases: 0
- Duplicate transcripts: 0
- Analysis status: 31 success, 0 failed, 0 invalid
- Raw mutation verification: pass
- Excluded-case reference verification: pass

## Warning Review

The initial audit had 29 warning cases, representing 33 warning instances.

- Real quality issues: 0
- Cosmetic warnings: 10
- Expected source limitations: 5
- Tooling false positives: 18

The real fix was to tighten the audit heuristics. Repeated speaker names were previously counted as navigation/footer boilerplate. The audit now warns only on repeated vendor/page/footer boilerplate. Cases without a formal Q&A heading remain analyzable when the section splitter can infer Q&A from call-transition language.

After cleanup, the remaining active warnings are:

- Repeated vendor/page boilerplate: 10
- Formal Q&A marker missing with Q&A inferred from transition: 4
- No Operator marker with host-led call flow possible: 1

## What Passed

- All active cases have canonical `raw/transcript.txt`.
- All active cases passed completeness gates.
- All active cases produced derived clean text, sections, speaker turns, weak labels, analysis outputs, and demo summaries.
- Raw transcript hashes matched before and after processing.
- No raw transcripts or PDFs are intended for repo commit.

## What Warnings Mean

Remaining audit warnings should be read as review prompts, not automatic failures. Vendor/page boilerplate is a source-format artifact handled by derived cleaning. Missing formal call-flow headings can be acceptable when the pipeline recovers a usable Q&A section and speaker turns.

Warnings should become blockers only when they indicate missing transcripts, short transcripts, blocked/login/paywall pages, duplicate transcript hashes, absent Q&A recovery, or invalid generated schemas.

## Label Evaluation Limits

Current gold-label files are scaffolds. Human labeling is still required.

- Weak labels are deterministic rule outputs, not gold labels.
- Weak-label counts are not model accuracy.
- No precision, recall, F1, or statistical performance claim is valid until human-reviewed gold labels are added.
- Empty gold-label files should be treated as `needs_human_labeling`.

## Next Corpus Expansion Criteria

Add cases only when a full public earnings-call transcript is available, provenance is recorded, raw transcript hashing is in place, audit gates pass, and derived section/speaker outputs are usable. New cases should not be included in evaluation claims until human gold labels exist for a representative subset.
