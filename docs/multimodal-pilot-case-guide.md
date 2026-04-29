# Multimodal Pilot Case Guide

## Purpose

This file defines the first tiny aligned case schema for future transcript-plus-audio-plus-video review work in Signal Engine 2.0.

It is intentionally small and conservative. The current pilot is a scaffold for future evidence collection, not proof of multimodal lift.

## Case Fields

- `id`: stable case identifier
- `domain`: support, sales, or account management
- `transcript_text`: the canonical review text
- `expected_signal_family`: seeded review label from the transcript benchmark
- `expected_review_action`: what a reviewer should do next
- `audio_file`: local path or `null`
- `video_file`: local path or `null`
- `transcript_evidence`: transcript terms or snippets that support the label
- `audio_expected_cues`: bounded cues worth checking if audio exists
- `video_expected_cues`: bounded cues worth checking if video exists
- `status`: `transcript_only_seed`, `ready_for_audio`, `ready_for_video`, or `complete`
- `limitations`: explicit boundary note for the case

## Boundaries

- Transcript evidence remains canonical.
- Audio and video are optional supporting cues only.
- Do not infer hidden intent, deception, or emotional truth from missing media.
- Use media only to prioritize review or clarify whether a transcript signal needs follow-up.

## What Makes A Case Useful

- The transcript already contains a human-reviewable signal.
- The expected review action is operational and concrete.
- Future audio or video would add bounded evidence rather than replace the transcript.

## Current State

- The seeded cases are transcript-safe and committed locally.
- Audio and video paths are `null` unless real aligned media exists.
- The pilot becomes measurement-ready only after the same cases have approved media plus reviewer labels.
