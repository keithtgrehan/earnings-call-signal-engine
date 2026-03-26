# Model Sidecars

This repo now includes an optional model-sidecar benchmark layer for inspecting how additional NLP models behave on top of existing processed cases.

The sidecars are additive only:
- deterministic transcript-first outputs remain the source of truth
- sidecars do not rewrite or weaken guidance, Q&A, or scorecard artifacts
- sidecars are for model-behavior comparison and review support only
- sidecars do not add trading automation or unsupported statistical claims

## Models

### `finbert_tone`
- Hugging Face id: `yiyanghkust/finbert-tone`
- Purpose: finance-domain tone classification for chunks, guidance spans, Q&A answers, and speaker turns
- Output: ranked label scores per text unit

### `financial_roberta`
- Hugging Face id: `soleimanian/financial-roberta-large-sentiment`
- Purpose: second finance-domain sentiment view for side-by-side comparison with FinBERT-Tone
- Output: ranked label scores per text unit

### `deberta_zero_shot`
- Hugging Face id: `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli`
- Purpose: configurable zero-shot scoring by finance-specific label groups
- Output: ranked scores per label group

### `mpnet_embeddings`
- Hugging Face id: `sentence-transformers/all-mpnet-base-v2`
- Purpose: semantic embedding baseline for nearest-neighbor and guidance-similarity inspection
- Output: embeddings plus similarity artifacts

## Supported Units

- `chunks`: transcript chunks from existing `chunks_scored.csv`
- `guidance_spans`: rows from existing `guidance.csv`
- `qa_answers`: answer text from existing `qa_pairs.json`
- `speaker_turns`: speaker-aware blocks from existing `transcript_sectioned.json` when present

The loader reuses existing repo artifacts. It does not add new parsing heuristics for these units.

## CLI

Run sidecars from the existing CLI with the explicit `sidecars` subcommand:

```bash
PYTHONPATH=src python -m earnings_call_sentiment sidecars \
  --case-id nvidia_q4_fy2024 \
  --models finbert_tone financial_roberta deberta_zero_shot mpnet_embeddings \
  --units chunks guidance_spans qa_answers speaker_turns \
  --zero-shot-label-config configs/model_eval/zero_shot_labels.finance.yaml
```

Useful flags:
- `--case-id`: one or more processed cases
- `--models`: one or more sidecar models
- `--units`: which existing artifacts to score
- `--zero-shot-label-config`: YAML label-group preset for the DeBERTa zero-shot model
- `--output-dir`: base directory for sidecar artifacts
- `--device`: `auto`, `cpu`, or `cuda`
- `--batch-size`
- `--max-length`

## Output Layout

Sidecar artifacts are written separately from the deterministic outputs:

```text
outputs/<case_id>/model_sidecars/
  finbert_tone/
    chunk_scores.jsonl
    guidance_span_scores.jsonl
    qa_answer_scores.jsonl
    speaker_turn_scores.jsonl
    run_summary.json
  financial_roberta/
    ...
  deberta_zero_shot/
    ...
  mpnet_embeddings/
    chunk_embeddings.jsonl
    guidance_span_embeddings.jsonl
    qa_answer_embeddings.jsonl
    speaker_turn_embeddings.jsonl
    chunk_similarity.json
    guidance_similarity.json
    qa_similarity.json
    speaker_turn_similarity.json
    run_summary.json
```

Each classification record includes:
- `case_id`
- `unit_type`
- `source_id`
- `section` if known
- `speaker` if known
- `text`
- `model_name`
- `label`
- `score`
- `rank`
- `metadata`

Each embedding record includes:
- `case_id`
- `unit_type`
- `source_id`
- `section` if known
- `speaker` if known
- `text`
- `model_name`
- `vector_dimension`
- `embedding`
- `metadata`

## Zero-Shot Label Presets

Two presets are included:
- `configs/model_eval/zero_shot_labels.default.yaml`
- `configs/model_eval/zero_shot_labels.finance.yaml`

The finance preset includes:
- `management_stance`
- `business_pressure`
- `qa_dynamics`
- `guidance_framing`

Each group is scored separately and saved with the label-group name in record metadata.

## Evaluation Script

Generate a compact sidecar comparison report:

```bash
PYTHONPATH=src python scripts/evaluate_model_sidecars.py \
  --case-id nvidia_q4_fy2024 \
  --sidecar-root outputs
```

This writes:
- `outputs/<case_id>/model_sidecars/model_sidecars_evaluation.json`
- `outputs/<case_id>/model_sidecars/model_sidecars_evaluation.md`

The report covers:
- coverage counts
- runtime per model
- label distributions
- FinBERT-Tone vs Financial-RoBERTa agreement where comparable
- disagreement hotspots
- MPNet similarity highlights
- an incremental-value summary scaffold

## Limitations

- Model downloads can be large and may take time on the first run.
- GPU is used automatically when `torch` sees CUDA, but GPU is not required.
- `speaker_turns` only runs when clean speaker-turn artifacts already exist.
- Prior-quarter guidance similarity uses existing `guidance_revision.csv` pairs when available; otherwise MPNet falls back to within-case nearest-neighbor outputs.
- Sidecars are local-first inspection aids. They do not replace deterministic outputs and should not be treated as trading signals.
