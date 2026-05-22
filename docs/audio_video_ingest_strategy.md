# Audio/Video Ingest Strategy

This rollout does not ingest audio or video. It adds metadata-only scaffolds for future rights-safe review.

## Audio

- Local/manual audio can be registered as metadata.
- ASR is the default future audio path when rights permit raw local processing.
- Diarization, timestamps, and confidence are optional metadata fields.
- YouTube and vendor media downloads are blocked by default.
- Source records must include audio availability, rights tier, source terms status, blocked reason, and raw-use permission.

## Video

- Video is metadata-only by default.
- Future video review must be sparse, transcript-aligned, and event-window based.
- Full-call video processing is out of scope.
- Source records must include video availability, rights tier, platform/source terms status, blocked reason, and raw-use permission.

## Event-Window Media Review

If rights-cleared media exists later, audio/video review should be constrained to transcript-aligned event windows such as guidance revisions, analyst friction, uncertainty spikes, or Q&A answer shifts. Media features are support evidence for reviewers, not canonical labels.

## Canonical Truth

Audio/video can support review, but deterministic transcript extraction remains the source of truth.
