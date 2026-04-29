# First Real Case Proof

## Status

- Case ID: `NVDA_2026_Q4`
- Expected raw transcript path: `data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt`
- Transcript present: `false`
- Status: `blocked: transcript missing`

No transcript text was downloaded, scraped, generated, or committed.

## Raw Transcript Handling

The raw transcript must remain local-only unless explicitly approved for commit. The path is covered by `.gitignore`:

```text
data/corpus/manual_cases/*/raw/*.txt
```

To confirm the local transcript is not staged or tracked after adding it manually:

```bash
git status --short data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt
git check-ignore -v data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt
```

## Manual Instructions

1. Manually confirm transcript reuse rights from the official NVIDIA investor-relations source or another lawful source.
2. Save the permitted local transcript as `data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt`.
3. Do not commit the raw transcript.
4. Re-run the weak-label baseline command below.

```bash
python scripts/run_weak_label_baseline.py --input data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt --case-id NVDA_2026_Q4 --out data/corpus/manual_cases/NVDA_2026_Q4/processed/weak_predictions.jsonl
```

## Weak Labels And Evaluation

- Weak labels are deterministic keyword/rule outputs.
- Draft labels are review aids only.
- No draft labels were created because the transcript is missing.
- Finalized manual labels are not present at `data/corpus/manual_cases/NVDA_2026_Q4/labels/gold_labels.jsonl`.
- Evaluation is blocked until finalized manual labels exist.

## Commands Run

- `test -f data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt`: transcript missing.
- Weak-label baseline: not run because transcript is missing.
- Gold-label validation/evaluation/error analysis: not run because finalized manual labels are missing.

## No-Claim Boundary

One case is not repeatability proof. This blocked status does not validate ML, product value, statistical significance, retrieval, or market correlation.

## Next Manual Action

Manually confirm transcript reuse rights for `NVDA_2026_Q4`, then save a legally safe local transcript at `data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt` without committing it.
