# Multimodal Pilot Status

- transcript_only_seed: `5`
- ready_for_audio: `3`
- ready_for_video: `2`
- complete: `0`
- cases_with_audio: `0`
- cases_with_video: `0`
- transcript_signal_coverage: `9`

## Status

- can_measure_multimodal_lift: `False`
- blocker: No aligned audio or video media is committed for the pilot cases yet, so multimodal lift cannot be measured honestly.

## Why This Matters

- The pilot schema is now ready for aligned transcript-plus-media collection.
- Transcript-only review still works today, and the media fields remain optional sidecars.
- No multimodal lift claim should be made until the same cases have aligned audio or video and gold review outcomes.

## Boundaries

- Audio and video remain supporting review cues only.
- Signals are review aids, not claims about hidden emotion, deception, or internal state.
