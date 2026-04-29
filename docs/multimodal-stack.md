# Multimodal Stack

Signal Engine 2.0 keeps a text-first canonical path and treats multimodal work as optional enrichment.

## Text-First Canonical Path

Canonical scoring today is:

1. ingest transcript JSON
2. normalize roles and transcript segments
3. apply deterministic lexicons, regexes, and turn-structure rules
4. emit scores, flags, and evidence

This path works fully offline and does not require external APIs or LLMs.

## Optional ASR

When a transcript is missing and only audio exists, an offline transcription step can be added before canonical scoring.

Potential tools:

- `faster-whisper`
- `WhisperX`

Constraint:

- ASR is an optional preprocessing step, not part of the canonical scoring logic

## Optional Diarization

Diarization can improve speaker separation before role mapping.

Potential tools:

- `pyannote.audio`

Constraint:

- diarization should remain optional because transcript-first scoring must stay usable without it

## Optional Audio Features

Audio enrichments can support review workflows around hesitation, interruptions, pace, pause behavior, and delivery quality.

Potential tools:

- `librosa`
- `torchaudio`
- `openSMILE`

Constraint:

- audio features should never replace transcript evidence in the canonical output schema

## Optional Video Keyframes

Video enrichments can help investigate flagged moments after deterministic text scoring has already isolated where to look.

Potential tools:

- `OpenCV`
- `PySceneDetect`
- `ffmpeg`
- `MoviePy`

Constraint:

- video analysis should be sparse and review-oriented, not a required first-pass dependency

## PII And Privacy

Recommended safeguards for multimodal workflows:

- keep transcript-first processing local where possible
- run PII detection/redaction before storing or sharing artifacts
- prefer storing references to flagged moments instead of copying raw media
- document provenance and access boundaries for audio/video sources

Presidio is a good optional candidate for deterministic PII detection and redaction.

## Cost Control

Signal Engine 2.0 should escalate only flagged moments.

Recommended flow:

1. run transcript-only scoring everywhere
2. isolate high-risk or high-opportunity turns
3. run audio/video enrichment only on those moments
4. keep multimodal review outputs separate from canonical truth
