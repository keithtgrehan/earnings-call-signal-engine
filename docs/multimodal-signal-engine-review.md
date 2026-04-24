# Multimodal Signal Engine Review

## Repo / Branch Baseline

- repo: `earnings-call-signal-engine-support-qa`
- branch: `signal-engine-2.0`
- implementation home: `src/signal_engine/multimodal/`

## Research / Data Sources Mapped

- transcript references for finance NLP, earnings calls, dialogue acts, support/sales intent, and uncertainty
- audio references for prosody tools and speech-emotion benchmarks
- video and multimodal references for bounded late-fusion planning
- current multimodal manifest count: `35`

See:

- `docs/dataset-and-research-map.md`
- `data/multimodal_research/research_manifest.json`

## Libraries Used Or Proposed

- used now:
  - `numpy`
  - `scikit-learn`
- optional only:
  - `librosa`
  - `opencv-python`
  - `mediapipe`
  - `transformers`

## What Was Implemented

- multimodal signal taxonomy
- multimodal research manifest generator
- typed multimodal schemas
- deterministic transcript cue extraction
- bounded audio feature extraction
- bounded video feature extraction
- conservative late fusion
- transcript-first feature extraction CLI
- transcript-only multimodal baseline wrapper
- scaffold multimodal evaluation protocol

## What Is Scaffolded Only

- multimodal lift evaluation
- aligned multimodal baseline training
- landmark-based visual review
- pretrained transformer emotion benchmarking

## Validation Target

- `python -m py_compile src/signal_engine/multimodal/*.py`
- multimodal pytest slices passed:
  - `tests/test_research_manifest.py`
  - `tests/test_multimodal_schemas.py`
  - `tests/test_text_features.py`
  - `tests/test_audio_features.py`
  - `tests/test_video_features.py`
  - `tests/test_fusion.py`
  - `tests/test_extract_multimodal_features_cli.py`
  - `tests/test_train_signal_baseline.py`
  - `tests/test_evaluate_multimodal_lift.py`
- legacy Signal Engine 2.0 tests remained green

## Safety / Boundary Notes

- transcript evidence remains canonical
- side cues are review aids, not hidden-state truth
- no lie detection, diagnosis, or unsupported body-language certainty

## Next Recommended Task

Build a tiny aligned transcript+audio fixture set with reviewer labels for uncertainty, friction, and escalation review so the evaluation scaffold can measure something real.
