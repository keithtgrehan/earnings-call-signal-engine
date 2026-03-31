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

## Cleanup Notes

- The original hardening summary overstated branch scope and treated non-empty artifacts as complete.
- The cleanup pass narrows scope by reverting unrelated app copy changes.
- Completion checks now require parseable sidecar JSON or JSONL artifacts, plus at least one JSONL record per selected unit before resume can skip work.
- Benchmark and evaluation outputs remain untracked runtime artifacts under `outputs/`.

## Known Limitations

- the repo currently contains three sidecar-ready processed demo cases, so the 5, 15, and 50 call manifests remain honest templates with placeholders
- DeBERTa remains slow on CPU even with reduced sampling; it is usable for smoke validation but not ideal for large local CPU batches
- broader throughput benchmarking is still better suited to NVIDIA hardware after the CPU path is validated
- sidecars remain optional comparison layers only; deterministic transcript-first outputs remain canonical
