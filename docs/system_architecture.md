# System Architecture

The Multimodal Communication Intelligence Engine is transcript-first. Text rules, weak labels, and local classifiers form the anchor; audio and video add bounded segment-level evidence when present.

## Pipeline

1. Ingest manifest-backed public, local, and gated dataset connectors.
2. Normalize every accepted row into the canonical v1 record schema and preserve rejected rows separately.
3. Align records into segment records with transcript-first timestamps and optional ASR/diarization readiness.
4. Score text signals, weak labels, emotion, and sentiment.
5. Extract audio/video features only when media exists and the event gate allows it.
6. Fuse modality evidence with text as anchor.
7. Ensemble all visible votes and disagreement flags.
8. Train/evaluate only when label support is honest enough.
9. Select a minimal active-learning review batch.

## Current Boundary

No API keys are required for the core path. Missing heavyweight or gated datasets/models are recorded as explicit skipped statuses. The current local fixture run does not include real audio/video-backed training data, so audio/video stages report limitation-aware outputs until aligned media is added.
