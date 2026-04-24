# Current Status

## Freeze Status
- The transcript-first deterministic core is currently frozen unless a real bug is found.
- The gold benchmark, active holdout, watchlist holdout, and behavior eval packages are currently frozen unless corruption or inconsistency is found.
- The current freeze boundary is documented in `docs/freeze-boundaries.md`.

## Implemented Now
- Transcript-first pipeline from call input to structured artifacts, with audio/video as optional supporting layers.
- Deterministic post-processing for guidance extraction, guidance revision comparison, and tone-change detection.
- Standard artifact outputs (`transcript.*`, `sentiment_segments.csv`, `chunks_scored.jsonl`, `guidance*.csv`, `tone_changes.csv`, `metrics.json`, `report.md`, `run_meta.json`).
- CLI stage controls (`--download-only`, `--transcribe-only`, `--score-only`) and output checks (`--strict`, `scripts/verify_outputs.py`).
- Conservative multimodal scaffolding for:
  - WhisperX alignment
  - optional pyannote diarization
  - OpenFace visual summaries
  - FinBERT and optional secondary emotion-model comparison
  - source/segment manifests and source-pair validation
  - external dataset registry placeholders for MAEC, MELD, and RAVDESS
  - multimodal coverage reporting

## Optional / Experimental
- Question-shift analysis (`--question-shifts`) is optional and heuristic-driven.
- LLM narrative layer in `scripts/run_eval.py` is optional; deterministic mode (`--llm none`) is the safest baseline.
- Backtest harness exists (`scripts/backtest_signals.py`) but depends on local run metadata quality and external price history inputs.
- Multimodal sidecars remain optional and supporting only. They do not replace transcript-first deterministic outputs.

## Current Multimodal Breadth
- Source manifests and segment manifests now exist under `data/source_manifests/`.
- Official transcript + replay/YouTube pairing is handled as manual-entry plus validation, not web crawling.
- External dataset support is registry/validation scaffolding only:
  - MAEC is the most domain-relevant external reference in this scaffold.
  - MELD and RAVDESS remain secondary calibration or sanity-check datasets only.
- The generated multimodal evaluation summary currently reports:
  - `12` source calls
  - `7` source/layout groups
  - `25` manifest segments
  - `0` current sources with alignment sidecar artifacts
  - `0` current sources with visual sidecar artifacts
  - `0` current sources with NLP sidecar artifacts

## Unproven
- No proven predictive edge from current repository artifacts.
- No statistical-significance claim should be made without dedicated out-of-sample evaluation.
- No claim of autonomous trading capability.
- No claim that the current multimodal sidecars improve benchmark quality or predictive performance.
- No claim that external dataset scaffolding proves finance-specific transfer performance.

## Practical Positioning
This project should be presented as a **transcript-first validated prototype** and deterministic evidence-backed review tool. The strongest current value is deterministic, evidence-linked output generation plus internal benchmark agreement checkpoints rather than return prediction.
