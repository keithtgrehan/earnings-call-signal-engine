# Multimodal Rights and AI Act Guardrails

Status: legal/ethical guardrail notes for research planning only. This is not legal advice and does not authorize data ingestion, model training, provider execution, or production deployment.

## EU AI Act risk framing

Multimodal affective analysis can move quickly into high-risk or prohibited territory when it claims to infer internal emotion, deception, identity, sensitive traits, or mental-health status. Signal Engine must keep any future multimodal work narrow, transcript-first, reviewer-support only, and limited to observable cue metadata for rights-cleared flagged windows.

The safe product frame is:

- Transcript remains canonical.
- Deterministic transcript extraction remains the source of truth.
- Multimodal metadata is optional reviewer context only.
- Outputs are observable cues only.
- No true emotion inference is claimed.

## Prohibited claims and uses

Signal Engine must not produce:

- emotion labels that claim internal state
- deception scores or deception detection
- mental-health diagnosis
- biometric identity inference
- personality scoring
- sensitive-trait inference
- workplace/education emotion inference
- relationship manipulation scoring
- trading, alpha, buy, sell, or live-execution claims
- universal emotion truth claims

The system must also avoid language that implies the same claims indirectly, such as saying a speaker "is lying," "is afraid," "is unstable," "loves you," or "can be manipulated."

## Biometric and privacy caution

Face, voice, body-pose, gaze, and action-unit metadata can become biometric or sensitive personal data depending on context, use, jurisdiction, and retention. Future work must avoid identity recognition, re-identification, face matching, voice matching, speaker identity inference, protected-trait inference, and persistent person-level profiling.

Allowed framing is narrow metadata over a rights-cleared window:

- pause_duration
- speech_rate
- overlap_count
- action_unit_metadata
- head_pose_metadata
- gaze_direction_metadata
- pose_landmark_metadata
- motion_intensity
- confidence and provenance

These fields must not be converted into true emotion, deception, health, identity, or workplace/education assessments.

## Consent and source-rights requirements

Before any local media metadata extraction, the project must have:

- rights-cleared source record
- source URL or manual-local provenance record
- consent or source-rights basis
- storage permission
- commit permission
- allowed modality list
- allowed feature list
- blocked-use notes
- deletion/export path when personal data is involved

Unknown rights, paywall bypass, scraped media, YouTube download, or unregistered raw media must fail closed.

## Raw media handling policy

- Do not commit raw audio/video/images.
- Do not download media for this research PR.
- Do not scrape YouTube.
- Do not ingest external datasets.
- Do not store provider outputs.
- Do not create embeddings, vector DBs, model weights, or training artifacts.
- Use metadata-only configs, schemas, docs, and tests.
- Restrict any future media audit to flagged windows only.

## Health-data exclusion

DAIC-WOZ and similar clinical or health-context resources are documented only as sensitive caution examples. They are excluded from Signal Engine product work, training, and gold-label creation unless a separate, explicit legal and ethics review approves a tightly scoped benchmark. No mental-health diagnosis is allowed.

## Workplace and education prohibition

Workplace/education emotion inference is prohibited. This includes evaluating candidates, employees, students, managers, analysts, executives, teachers, or learners based on inferred emotion, deception, attention, mental state, productivity, competence, or personality from multimodal cues.

## Required output limits

Every future cue record must include interpretation limits stating that it:

- does_not_infer_true_emotion
- does_not_detect_deception
- does_not_score_personality
- is_not_canonical_signal

If an output cannot satisfy those limits, it must be blocked.
