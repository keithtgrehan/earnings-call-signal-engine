# Model Sidecars Runtime Hardening Summary

## What Was Added

- tracked `src/earnings_call_sentiment/model_sidecars/models/` adapters and fixed the ignore rule that previously hid them from git
- `sidecars-prewarm` CLI entrypoint for explicit model cache warmup
- `sidecars-benchmark` CLI path plus `scripts/benchmark_model_sidecars.py`
- reduced CPU validation controls: `--limit`, `--sample-size`, `--sample-strategy`, `--seed`
- resume and retry behavior with artifact-completeness checks and `.inprogress` temp writes
- benchmark JSON and Markdown outputs under `outputs/<case_id>/model_sidecars/benchmarks/`
- richer evaluation reports with sidecar-vs-sidecar and deterministic-vs-sidecar disagreement hotspots
- manifest loader plus 5, 15, and 50 call manifest templates
- optional lighter zero-shot fallback: `distilbart_zero_shot_smoke`

## Commands Run

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars-prewarm --models finbert_tone financial_roberta deberta_zero_shot mpnet_embeddings --device cpu
PYTHONPATH=src python3 scripts/benchmark_model_sidecars.py --case-id nvidia_q4_fy2024 --models finbert_tone --units chunks --sample-size 4 --sample-strategy head --batch-size 4 --device cpu --run-mode warm --output-dir outputs
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars --case-id nvidia_q4_fy2024 --models deberta_zero_shot --units guidance_spans qa_answers --zero-shot-label-config configs/model_eval/zero_shot_labels.finance.yaml --output-dir outputs --device cpu --batch-size 2 --sample-size 3 --sample-strategy random --seed 7 --prewarm
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars --case-id nvidia_q4_fy2024 --models mpnet_embeddings --units guidance_spans qa_answers --output-dir outputs --device cpu --batch-size 2 --sample-size 3 --sample-strategy random --seed 7 --prewarm
PYTHONPATH=src python3 scripts/evaluate_model_sidecars.py --case-id nvidia_q4_fy2024 --sidecar-root outputs
```

## Artifacts Produced

- `outputs/nvidia_q4_fy2024/model_sidecars/benchmarks/model_sidecars_benchmark.json`
- `outputs/nvidia_q4_fy2024/model_sidecars/benchmarks/model_sidecars_benchmark.md`
- `outputs/nvidia_q4_fy2024/model_sidecars/deberta_zero_shot/guidance_span_scores.jsonl`
- `outputs/nvidia_q4_fy2024/model_sidecars/deberta_zero_shot/qa_answer_scores.jsonl`
- `outputs/nvidia_q4_fy2024/model_sidecars/deberta_zero_shot/run_summary.json`
- `outputs/nvidia_q4_fy2024/model_sidecars/mpnet_embeddings/guidance_span_embeddings.jsonl`
- `outputs/nvidia_q4_fy2024/model_sidecars/mpnet_embeddings/guidance_similarity.json`
- `outputs/nvidia_q4_fy2024/model_sidecars/mpnet_embeddings/qa_answer_embeddings.jsonl`
- `outputs/nvidia_q4_fy2024/model_sidecars/mpnet_embeddings/qa_similarity.json`
- `outputs/nvidia_q4_fy2024/model_sidecars/mpnet_embeddings/run_summary.json`
- `outputs/nvidia_q4_fy2024/model_sidecars/model_sidecars_evaluation.json`
- `outputs/nvidia_q4_fy2024/model_sidecars/model_sidecars_evaluation.md`

## Known Limitations

- the repo currently contains three sidecar-ready processed demo cases, so the 5, 15, and 50 call manifests remain honest templates with placeholders
- DeBERTa remains slow on CPU even with reduced sampling; it is usable for smoke validation but not ideal for large local CPU batches
- broader throughput benchmarking is still better suited to NVIDIA hardware after the CPU path is validated
- sidecars remain optional comparison layers only; deterministic transcript-first outputs remain canonical
