# Audio/Video Ingest Strategy

This rollout does not ingest audio or video. It adds metadata-only scaffolds for future rights-safe review.

## Audio

- Local/manual audio can be registered as metadata.
- ASR is the default future audio path when rights permit raw local processing.
- Diarization, timestamps, and confidence are optional metadata fields.
- YouTube and vendor media downloads are blocked by default.

## Video

- Video is metadata-only by default.
- Future video review must be sparse, transcript-aligned, and event-window based.
- Full-call video processing is out of scope.

## Canonical Truth

Audio/video can support review, but deterministic transcript extraction remains the source of truth.
