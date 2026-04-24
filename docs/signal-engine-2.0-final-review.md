# Signal Engine 2.0 Final Review

## What Changed

- added proof-oriented docs for evaluation, hero output, and a simple recruiter-readable architecture summary
- added an offline-safe NLP research manifest with 22 transcript-first research entries
- added a text-baseline training workflow that reports insufficient data honestly instead of inventing metrics
- added a multimodal research manifest with 35 transcript/audio/video/multimodal references
- added bounded multimodal schemas, text/audio/video feature extraction, conservative fusion, and scaffold evaluation scripts
- kept transcript-first deterministic output canonical throughout

## Files Changed

Primary areas:

- `README.md`
- `docs/`
- `scripts/`
- `src/signal_engine/`
- `tests/`
- `data/nlp_research/`
- `data/multimodal_research/`

## Commands Run

- `python scripts/build_nlp_research_manifest.py`
- `python scripts/train_signal_text_baseline.py`
- `python scripts/build_research_manifest.py`
- `python scripts/train_signal_baseline.py`
- `python scripts/evaluate_multimodal_lift.py`
- `python scripts/extract_multimodal_features.py --text-file data/signal_engine_2_0/fixtures/support_tickets_realistic.jsonl --domain support --redact-pii --out outputs/signal_engine_2_0/multimodal_feature_report.json`
- validation commands listed in the repo task plan

## Validation Results

Completed in this branch:

- `python -m py_compile src/signal_engine/*.py src/signal_engine/adapters/*.py scripts/*.py`
- `python -m py_compile src/signal_engine/multimodal/*.py`
- `make portfolio-ci`
- `python scripts/run_signal_engine_2_0_demo.py`
- all requested tranche-one and tranche-two pytest slices passed

Observed outcomes:

- `make portfolio-ci` passed
- final demo passed
- deterministic text-emotion benchmark remained green
- optional transformer benchmark ran successfully from local cache during the demo run

## What Works Now

- transcript-first deterministic review for support, sales, account management, and earnings-call proof bundles
- optional PII redaction before deterministic analysis
- deterministic text-emotion benchmark workflow
- offline-safe NLP research manifest
- weak-label text-baseline training path with honest insufficient-data handling
- multimodal taxonomy, research map, feature schemas, and bounded text/audio/video scaffolds

## What Remains Roadmap

- stronger labeled corpora for transcript benchmark work
- aligned multimodal fixtures for real lift measurement
- production ASR, diarization, and richer audio/video sidecars
- optional transformer and retrieval benchmarks backed by approved local caches

## NLP Research / Modeling Status

- transcript-focused research manifest exists and is reproducible
- current local weak-label corpus contains 24 utterance-level examples from committed Signal Engine 2.0 fixtures
- current weak-label support:
  - `risk_friction`: 14
  - `opportunity_commitment`: 9
  - `uncertainty_hedging`: 1
  - `neutral`: 0
- the text baseline therefore exits with `insufficient_data` instead of training a misleading 4-class model

## Known Blockers

- no aligned multimodal gold fixtures are committed in the current Signal Engine 2.0 path
- optional transformer benchmarking still depends on local cache and dependency availability outside machines like this one

## Recommended Next Step

Create a small human-reviewed transcript label set for `signal_family` and run a first honest transcript-only benchmark before claiming any model lift.
