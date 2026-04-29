# Manual Transcript Download Guide

Manual transcript intake is deliberately separate from automation. The repo should not silently pull raw transcripts or vendor content.

## Case Setup

Use `scripts/build_manual_corpus_case.py` to create an empty case folder and checklist from a manifest row.

```bash
python scripts/build_manual_corpus_case.py --manifest data/corpus_manifest.example.csv --case-id NVDA_2026_Q4 --out-root /tmp/manual_cases
```

## Manual Requirements

- Confirm source rights and access.
- Confirm company, ticker, fiscal period, call date, and source URL.
- Save only transcript text you are allowed to use.
- Keep raw transcript text out of git unless explicitly approved.
- Record source notes and blocked reasons instead of deleting hard cases.
- Label only after sectioning, speaker roles, and evidence spans are reviewable.

## No-Claim Boundary

A folder scaffold is not a corpus. A downloaded transcript is not a labelled benchmark. A weak label is not a manual gold label.
