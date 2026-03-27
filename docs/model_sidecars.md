# Model Sidecars

This repo includes an optional model-sidecar layer for comparing additional NLP model behavior on top of existing processed cases.

The sidecars are additive only:
- deterministic transcript-first outputs remain the source of truth
- sidecars do not rewrite guidance, Q&A, scorecard, or report artifacts
- sidecars are for inspection, comparison, and utility benchmarking only
- sidecars do not add trading automation or unsupported statistical claims

## What Sidecars Are Not

- not a rewrite of the deterministic pipeline
- not a replacement for transcript-backed evidence rows
- not a claim of alpha, predictive lift, or statistical validity
- not a hidden cloud dependency path

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

### `distilbart_zero_shot_smoke`
- Hugging Face id: `valhalla/distilbart-mnli-12-1`
- Purpose: lighter optional zero-shot fallback for CPU smoke tests
- Output: ranked scores per label group
- Note: this is a lower-cost fallback, not the canonical benchmark zero-shot model

### `mpnet_embeddings`
- Hugging Face id: `sentence-transformers/all-mpnet-base-v2`
- Purpose: semantic embedding baseline for nearest-neighbor and guidance-similarity inspection
- Output: embeddings plus similarity artifacts

## Supported Units

- `chunks`: transcript chunks from existing `chunks_scored.csv`
- `guidance_spans`: rows from existing `guidance.csv`
- `qa_answers`: answer text from existing `qa_pairs.json`
- `speaker_turns`: speaker-aware blocks from existing `transcript_sectioned.json` when present

The loader reuses existing repo artifacts. It does not invent new parsing heuristics for these units.

## Prewarm

Use prewarm to download and initialize models before a timed benchmark run:

```bash
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars-prewarm \
  --models finbert_tone financial_roberta deberta_zero_shot mpnet_embeddings \
  --device cpu
```

Prewarm:
- resolves optional dependencies
- initializes pipelines or embedding models
- downloads model weights and tokenizers if they are not already cached
- exits cleanly with a clear error if an optional dependency is missing

## Running Sidecars

Run sidecars on an existing processed case:

```bash
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars \
  --case-id nvidia_q4_fy2024 \
  --models finbert_tone financial_roberta deberta_zero_shot mpnet_embeddings \
  --units chunks guidance_spans qa_answers \
  --zero-shot-label-config configs/model_eval/zero_shot_labels.finance.yaml \
  --output-dir outputs
```

Useful flags:
- `--prewarm`: initialize the requested models before scoring
- `--force`: recompute even when complete sidecar artifacts already exist
- `--no-resume`: disable skip/resume behavior and run selected model/unit outputs again
- `--limit`: head limit per unit type before sampling
- `--sample-size`: sampled item count per unit type
- `--sample-strategy`: `head`, `random`, or `stratified`
- `--seed`: deterministic seed for random sampling
- `--device`: `auto`, `cpu`, or `cuda`
- `--batch-size`
- `--max-length`

## Reduced CPU Validation

The slower zero-shot and embedding models can be validated on CPU with reduced runs:

```bash
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars \
  --case-id nvidia_q4_fy2024 \
  --models deberta_zero_shot mpnet_embeddings \
  --units qa_answers guidance_spans \
  --sample-size 4 \
  --sample-strategy random \
  --seed 7 \
  --batch-size 2 \
  --device cpu \
  --prewarm
```

Recommended CPU pattern:
- prewarm first
- use `--sample-size` or `--limit` for smoke validation
- keep `--batch-size` small for the heavier CPU-only models

## Resume And Retry

Resume/skip behavior is enabled by default.

Completion rules:
- classification output is complete when the final unit JSONL exists and is non-empty
- embedding output is complete when the final embedding JSONL and similarity JSON both exist and are non-empty
- temporary `.inprogress` files do not count as complete

Write safety:
- sidecar unit artifacts are written to temporary `.inprogress` files first
- final files are only moved into place after a full successful write
- interrupted runs can resume and skip already completed model/unit artifacts

Recompute controls:
- use `--force` to recompute selected outputs
- use `--no-resume` to disable skip logic for a run

## Benchmarks

Benchmark sidecars with a dedicated script or the matching CLI entrypoint:

```bash
PYTHONPATH=src python3 scripts/benchmark_model_sidecars.py \
  --case-id nvidia_q4_fy2024 \
  --models finbert_tone financial_roberta \
  --units chunks guidance_spans \
  --batch-size 4 \
  --device cpu \
  --run-mode warm
```

Or:

```bash
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars-benchmark \
  --manifest configs/model_eval/manifests/cpu_smoke_5_calls.template.yaml
```

Benchmark reports record:
- per-model wall-clock runtime
- per-unit item counts
- items per second
- requested device and resolved runtime device
- batch size and max length
- warm or cold run label
- approximate peak process RSS where available
- output paths for generated sidecar artifacts

Memory note:
- peak memory is approximate process-level RSS from `resource.ru_maxrss` where available
- this is useful for honest comparison, but it is not an isolated cross-platform profiler

## Evaluation Reports

Generate a comparison report from existing sidecar outputs:

```bash
PYTHONPATH=src python3 scripts/evaluate_model_sidecars.py \
  --case-id nvidia_q4_fy2024 \
  --sidecar-root outputs
```

The evaluation report writes:
- `outputs/<case_id>/model_sidecars/model_sidecars_evaluation.json`
- `outputs/<case_id>/model_sidecars/model_sidecars_evaluation.md`

It covers:
- coverage counts
- runtime per model
- label distributions
- FinBERT-Tone vs Financial-RoBERTa agreement where comparable
- sidecar disagreement hotspots
- deterministic chunk-sentiment vs sidecar disagreement hotspots where meaningful
- MPNet similarity highlights
- an incremental-value summary scaffold

These are inspection reports only. They are not accuracy claims.

## Output Layout

Sidecar artifacts are written separately from deterministic outputs:

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
  distilbart_zero_shot_smoke/
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
  benchmarks/
    model_sidecars_benchmark.json
    model_sidecars_benchmark.md
  model_sidecars_evaluation.json
  model_sidecars_evaluation.md
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

Included presets:
- `configs/model_eval/zero_shot_labels.default.yaml`
- `configs/model_eval/zero_shot_labels.finance.yaml`

The finance preset includes:
- `management_stance`
- `business_pressure`
- `qa_dynamics`
- `guidance_framing`

Each label group is scored separately and saved with the label-group name in record metadata.

## Batch Manifest Templates

Templates live under:
- `configs/model_eval/manifests/cpu_smoke_5_calls.template.yaml`
- `configs/model_eval/manifests/gpu_batch_15_calls.template.yaml`
- `configs/model_eval/manifests/gpu_batch_50_calls.template.yaml`

Current repo reality:
- the repo currently contains three sidecar-ready processed demo cases: `meta_q3_2022`, `netflix_q1_2022`, and `nvidia_q4_fy2024`
- the 5, 15, and 50 call manifests are therefore honest templates with placeholders where additional processed cases are still needed

## Limitations

- first-run model downloads can be large and slow on CPU
- GPU is used automatically when `torch` sees CUDA, but GPU is not required
- `speaker_turns` only runs when clean speaker-turn artifacts already exist
- prior-quarter guidance similarity uses existing `guidance_revision.csv` pairs when available; otherwise MPNet falls back to within-case nearest-neighbor outputs
- broader throughput benchmarking is better suited to NVIDIA hardware after CPU-side validation
- sidecars remain optional support layers and should not be treated as trading signals
