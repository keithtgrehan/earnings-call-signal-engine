# Reproducibility Check

## Summary

Critical proof artifacts can be regenerated only partially from the current committed source without manual review. Evaluation reports and the lightweight signal retrieval index are reproducible apart from expected timestamp drift. The pilot corpus rebuild currently produces material artifact drift and should not replace committed proof artifacts without human confirmation.

Full validation after restoring the committed pilot proof artifacts passed with `342` tests.

## Commands Run

- `python tools/run_evaluation_loop.py`
- `python tools/run_next_experiment.py || true`
- `python tools/run_embedding_benchmark.py || true`
- `python tools/nlp_assets/audit_assets.py || true`
- `python tools/nlp_assets/download_assets.py --safe-only`
- `python tools/nlp_assets/validate_assets.py`
- `python tools/nlp_assets/summarize_assets.py`
- `PYTHONPATH=src python scripts/build_pilot_corpus.py --target-count 20 --embedding-provider hashing`
- `PYTHONPATH=src python scripts/validate_pilot_corpus.py`
- `python scripts/build_signal_retrieval_index.py`

## Results

| artifact area | result | notes |
| --- | --- | --- |
| Evaluation reports | pass | Metrics regenerated for 57 gold labels with precision `0.3205`, recall `0.4499`, and F1 `0.3743`. |
| Experiment reports | pass/gated | Local ML experiment selected; embedding benchmark skipped because only 57 gold labels exist and retrieval experiment mode was not enabled. |
| NLP asset registry | pass with external-source drift | Safe SEC company ticker download worked, but the live SEC JSON hash differed from the committed hash. The committed registry hash was restored and should be reviewed before replacement. |
| Signal retrieval index | pass with timestamp-only drift | `data/nlp_research/signal_retrieval_index.json` differed only in `generated_at`; committed output was restored. |
| Pilot corpus artifacts | material drift | Rebuild changed `data/corpus/reports/pilot_corpus_summary.json` schema and temporarily removed representative committed sample artifacts before regeneration completed. |
| Pilot corpus validation | blocked during drift run | Validation failed while regenerated artifacts were temporarily absent. Committed artifacts were restored. |

## Drift Summary

Material pilot corpus differences observed:

- `data/corpus/reports/pilot_corpus_summary.json` changed from `retrieval_index_output_dir` to a nested `retrieval_index` object.
- `committed_samples` changed from committed artifact paths to case-id lists.
- `generated_at` changed as expected.
- The rebuild temporarily deleted:
  - `data/corpus/manifests/pilot_corpus_manifest.csv`
  - `data/corpus/manifests/pilot_corpus_manifest.jsonl`
  - `data/corpus/reports/pilot_corpus_summary.json`
  - representative `LLY_2025_Q2_call08` processed sample artifacts

## Decision

Materially different regenerated proof artifacts were not accepted. The committed manifests, representative samples, retrieval schemas, and tiny proof artifacts were restored.

## Required Human Confirmation Before Replacement

Keith should confirm whether the newer pilot corpus summary schema is preferred. If yes, update the tests/docs together and regenerate the pilot corpus in one intentional commit. Until then, keep the current committed artifacts as the stable proof record.
