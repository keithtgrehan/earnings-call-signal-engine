# Audio Pilot Intake Guide

## Purpose

This intake sheet prepares the first aligned audio pilot without inventing media paths or pretending the media already exists.

## Output File

- `data/multimodal_research/audio_pilot_intake.csv`

## Required Fields For Future Audio Clips

- `audio_file_to_add`
- `audio_start_seconds`
- `audio_end_seconds`
- `audio_rights_confirmed`
- `reviewer_notes`

## Suggested Next Collection Pass

Add `4` to `6` real clips later, using cases that already have strong transcript evidence:

- support dispute / escalation
- sales procurement blocker
- hedged pricing response
- renewal-risk account review

## Rules

- do not invent audio paths
- do not mark rights as confirmed unless approval actually exists
- keep transcript evidence canonical
- use audio only as a supporting review cue, not a truth source

## Validation

Run:

```bash
python scripts/validate_audio_pilot_assets.py
```

If no approved aligned audio exists yet, the validator should return a blocked status rather than failing the proof loop.
