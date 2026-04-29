# Multimodal Signal Taxonomy

## Goal

Design a transcript-first multimodal signal engine that surfaces bounded review cues across transcript, audio, and video inputs.

## Explicit Non-Goals

- no truth detection
- no lie detection
- no psychological diagnosis
- no unsupported emotion certainty
- no trading automation

## Signal Taxonomy

### Transcript signals

- uncertainty
- hedging
- guidance change
- analyst pressure
- evasive answer
- reassurance
- contradiction
- sentiment shift
- escalation risk

### Audio signals

- pause length
- speech-rate change
- pitch variation
- volume/intensity change
- overlap/interruption
- hesitation markers

### Visual signals

- face visibility
- gaze direction shift
- head movement
- gesture intensity
- posture shift
- expression change

## Output Fields

- `signal_name`
- `modality`
- `strength`: `low | medium | high`
- `evidence_span` or `evidence_window`
- `confidence`
- `reason`
- `recommended_review_action`

## Boundary Language

Signals are review cues, not claims about internal state.

Transcript evidence remains canonical. Audio and video cues can support reviewer attention, but they should not override the deterministic transcript-backed interpretation.
