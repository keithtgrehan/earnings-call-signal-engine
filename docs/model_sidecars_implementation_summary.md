# Model Sidecars Implementation Summary

## What Was Added

- New optional `model_sidecars` package under `src/earnings_call_sentiment/model_sidecars/`
- Four model adapters:
  - `finbert_tone`
  - `financial_roberta`
  - `deberta_zero_shot`
  - `mpnet_embeddings`
- Case/artifact loaders that reuse existing processed-case outputs for:
  - `chunks`
  - `guidance_spans`
  - `qa_answers`
  - `speaker_turns`
- Separate sidecar artifact writing under `outputs/<case_id>/model_sidecars/`
- New CLI path:
  - `python -m earnings_call_sentiment sidecars ...`
- New zero-shot label presets:
  - `configs/model_eval/zero_shot_labels.default.yaml`
  - `configs/model_eval/zero_shot_labels.finance.yaml`
- New evaluation script:
  - `scripts/evaluate_model_sidecars.py`
- New docs:
  - `docs/model_sidecars.md`
- Focused sidecar tests plus compatibility fixes needed to keep the broader suite green

## Commands To Run

### Sidecars

```bash
PYTHONPATH=src python -m earnings_call_sentiment sidecars \
  --case-id nvidia_q4_fy2024 \
  --models finbert_tone financial_roberta deberta_zero_shot mpnet_embeddings \
  --units chunks guidance_spans qa_answers \
  --zero-shot-label-config configs/model_eval/zero_shot_labels.finance.yaml \
  --output-dir outputs
```

### Evaluation

```bash
PYTHONPATH=src python scripts/evaluate_model_sidecars.py \
  --case-id nvidia_q4_fy2024 \
  --sidecar-root outputs
```

### Tests

```bash
python -m pytest -q
```

## Validation Performed

- Full test suite:
  - `144 passed in 28.32s`
- Real local case artifacts generated successfully for `nvidia_q4_fy2024`:
  - `outputs/nvidia_q4_fy2024/model_sidecars/finbert_tone/`
  - `outputs/nvidia_q4_fy2024/model_sidecars/financial_roberta/`
- Real local evaluation report generated:
  - `outputs/nvidia_q4_fy2024/model_sidecars/model_sidecars_evaluation.json`
  - `outputs/nvidia_q4_fy2024/model_sidecars/model_sidecars_evaluation.md`

Observed real-case runtime summaries on CPU:
- `finbert_tone`: `52.9141s`
- `financial_roberta`: `166.4491s`

Observed real-case comparison summary:
- comparable rows: `133`
- agreement rows: `103`
- disagreement rows captured in report: `10`
- agreement rate: `0.7744`

## Known Limitations

- First-time model downloads and initialization for `deberta_zero_shot` and `mpnet_embeddings` can be materially slower on CPU than the two finance classifiers.
- The real local validation completed for the two finance classifiers and the evaluation script; the larger first-time zero-shot / embedding runs remain the slowest path on local CPU-only execution.
- `speaker_turns` only runs when clean speaker-turn artifacts already exist.
- Prior-quarter guidance similarity uses existing `guidance_revision.csv` pairs when available; otherwise MPNet falls back to within-case nearest-neighbor similarity.
- Sidecars remain optional supporting layers only. Deterministic transcript-first outputs remain canonical.

## Files Changed

- Modified:
  - `README.md`
  - `app/site_server.py`
  - `app/templates/index.html`
  - `pyproject.toml`
  - `requirements.txt`
  - `src/earnings_call_sentiment/cli.py`
- Added:
  - `configs/model_eval/zero_shot_labels.default.yaml`
  - `configs/model_eval/zero_shot_labels.finance.yaml`
  - `docs/model_sidecars.md`
  - `docs/model_sidecars_implementation_summary.md`
  - `scripts/evaluate_model_sidecars.py`
  - `src/earnings_call_sentiment/model_sidecars/`
  - `tests/test_evaluate_model_sidecars.py`
  - `tests/test_model_sidecars_cli.py`
  - `tests/test_model_sidecars_config.py`
  - `tests/test_model_sidecars_embeddings.py`
  - `tests/test_model_sidecars_failure.py`
  - `tests/test_model_sidecars_io.py`
  - `tests/test_model_sidecars_registry.py`
