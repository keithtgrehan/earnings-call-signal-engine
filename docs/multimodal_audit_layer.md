# Multimodal Audit Layer

Status: design guardrail only. This file documents architecture and contracts for future selective audit work. It does not implement raw media ingestion, media download, training, production emotion recognition, or provider execution.

## Architecture

1. Deterministic transcript signal
   - Transcript remains canonical.
   - Existing deterministic extraction produces evidence spans for hedging, uncertainty, reassurance, answer shift, analyst pressure, and related finance cues.
2. Flagged window selector
   - Converts transcript-backed signals into small review windows.
   - The design is flagged windows only.
   - It excludes full-call brute-force multimodal processing.
3. Rights/consent gate
   - Requires rights-cleared source records before any media metadata work.
   - Blocks unknown, restricted, scraped, or unregistered media.
4. Audio metadata extractor placeholder
   - Future optional adapter for pause_duration, speech_rate, filler_count, pitch_f0_summary, energy_summary, asr_confidence, diarization_confidence, overlap_count, turn_taking_latency, and interruption_count.
   - Metadata only; no true emotion inference.
5. Video metadata extractor placeholder
   - Future optional adapter for action_unit_metadata, head_pose_metadata, gaze_direction_metadata, pose_landmark_metadata, motion_intensity, shot_change_count, and speaking_presence_metadata.
   - Metadata only; no biometric identity inference.
6. Multimodal cue record
   - Stores allowed observable cue metadata, confidence, interpretation limits, and provenance.
   - canonical_status must be reviewer_support_only.
7. Reviewer UI/output layer
   - Shows metadata as reviewer-support only context.
   - Must avoid labels that imply true emotion, deception, mental health, identity, or personality.
8. Evaluation gate
   - Measures reviewer usefulness, unsupported claim rate, citation quality, abstain behavior, and calibration.
   - Does not promote multimodal metadata to Signal Engine gold labels.
9. Audit log
   - Records source rights, window ID, extractor version, run timestamp, feature names, confidence, and blocked reasons.

## Transcript-first canonical flow

```text
transcript
  -> deterministic signal extraction
  -> evidence spans
  -> flagged window selector
  -> rights/consent gate
  -> optional audio/video metadata placeholders
  -> multimodal cue record
  -> reviewer-support only output
  -> evaluation and audit log
```

The deterministic transcript signal remains the source of truth. Multimodal metadata cannot create, promote, delete, or override canonical signals.

## Escalation triggers

Escalation to optional metadata review is allowed only when a transcript-backed candidate already exists and a reviewer-support cue could help adjudication:

- high uncertainty or hedging density
- management answer shift after analyst pressure
- overlapping Q&A turns in a flagged window
- apparent contradiction / inconsistency that needs timestamped context
- unusually long transcript pause marker or unclear turn boundary
- low ASR or diarization confidence for a narrow segment

Escalation is blocked when rights are unknown, when a window is not transcript-backed, or when the requested output is a banned claim.

## Input contract

Required inputs:

- transcript_window_ref
- deterministic_signal_ids
- evidence_span_refs
- source_rights_record_id
- media_availability_status
- allowed_modalities
- requested_features
- reviewer_context_purpose

Inputs must not include raw media bodies in committed artifacts. Any local media reference must point to a manual-local, rights-cleared record and remain outside the repository unless a separate policy explicitly permits storage.

## Output contract

Allowed outputs:

- record_id
- source_type
- canonical_status: reviewer_support_only
- transcript_window_ref
- feature_metadata
- extractor_confidence
- provenance
- interpretation_limits
- blocked_reason

Banned outputs:

- raw_text
- raw_audio
- raw_video
- emotion_label
- deception_score
- manipulation_score
- mental_health_label
- biometric_identity
- personality_score
- sensitive_trait_inference
- workplace_emotion_inference
- education_emotion_inference
- trading or alpha claims
- relationship manipulation suggestions

## Provenance requirements

Every cue record must include:

- source_rights_record_id
- transcript_window_ref
- deterministic_signal_ids
- extractor_name
- extractor_version
- feature_schema_version
- run_timestamp
- media_storage_status
- rights-cleared confirmation
- blocked_reason when extraction is skipped

## Reviewer-only UX language

Use language such as:

- "Observable cue metadata"
- "Reviewer-support only"
- "Not canonical"
- "Does not infer true emotion"
- "Does not detect deception"
- "Source rights verified"

Do not use language such as:

- "This person is lying"
- "This person feels afraid"
- "Manipulation score"
- "Mental health signal"
- "Personality profile"
- "Body language truth"

## Confidence limits

Confidence fields describe extractor reliability or measurement quality. They do not describe confidence in a person's internal state. Low confidence must trigger abstention or blocked output. High confidence does not authorize emotion, deception, identity, workplace, education, relationship, or trading claims.

## Storage rules

- Store schemas, configs, docs, and small metadata examples only.
- Do not commit raw transcript/audio/video/image files for this layer.
- Do not commit embeddings, model weights, vector DBs, provider outputs, or bulky artifacts.
- Keep local manual media references outside git unless an explicit rights-cleared storage policy allows otherwise.
- Store only flagged-window metadata, not full-call multimodal traces.

## No full-call brute-force processing

The default is no full-call brute-force multimodal processing. Any future audio/video audit must be flagged-window-only, rights-cleared, manual/local or otherwise explicitly registered, and reviewer-support only.
