# Multimodal Affective Cue Research

Status: research and registry guardrails only. This document does not authorize raw audio/video ingestion, media downloads, YouTube scraping, external dataset ingestion, model training, production emotion-recognition models, or provider execution.

## Framing

Transcript remains canonical. The Signal Engine source of truth remains deterministic transcript extraction with evidence spans, provenance, and human adjudication. Multimodal review can only add reviewer-support only metadata for already flagged transcript windows.

The intended object is observable affective cues only: pauses, turn-taking latency, overlap, filler counts, action-unit metadata, pose metadata, and related confidence summaries. These are behavioral or measurement metadata, not claims about internal state. The system must make no true emotion inference, no deception detection, no mental-health diagnosis, no biometric identity inference, no workplace/education emotion inference, no relationship manipulation scoring, and no universal emotion truth claim.

## Why this is not emotion reading

The layer is explicitly not an "emotion reading" system. A pause, gaze direction estimate, or speech-rate change can be caused by many factors: audio quality, latency, prepared remarks, speech style, role, language, disability, stress, room setup, camera angle, or transcription errors. A reviewer can inspect such metadata as context, but the metadata must not be converted into labels such as "angry," "afraid," "lying," "manipulative," or "mentally unwell."

Safe framing:

- observable cues only
- reviewer-support only
- flagged windows only
- no true emotion inference
- no deception detection
- no mental-health diagnosis
- no biometric identity inference
- no workplace/education emotion inference

## Feature taxonomy

Transcript features remain the canonical extraction surface:

- hedging
- uncertainty
- reassurance
- answer shift
- politeness / pressure
- confidence language
- contradiction / inconsistency
- lexical financial tone

Audio metadata features are optional reviewer context, only for rights-cleared flagged windows:

- pause_duration
- speech_rate
- filler_count
- pitch_f0_summary
- energy_summary
- asr_confidence
- diarization_confidence
- overlap_count
- turn_taking_latency
- interruption_count

Video metadata features are optional reviewer context, only for rights-cleared flagged windows:

- action_unit_metadata
- head_pose_metadata
- gaze_direction_metadata
- pose_landmark_metadata
- motion_intensity
- shot_change_count
- speaking_presence_metadata

## Model and tool candidates

These candidates are research only. Listing them does not approve production use, training, media download, raw media commit, or external provider execution.

| Candidate | Modality | Potential use | Guardrail |
| --- | --- | --- | --- |
| transcript-first deterministic cue rules | text | Canonical extraction of hedging, uncertainty, reassurance, answer shift, and evidence spans | Source of truth; no internal emotion labels |
| openSMILE / eGeMAPS | audio metadata | Prosody and voice-quality summaries for flagged windows | Metadata only; no emotion label |
| wav2vec / HuBERT / WavLM | audio representation | Research comparison for ASR confidence or acoustic metadata | Benchmark only; no production inference |
| emotion2vec | audio research | Literature review of affective representation approaches | Do not emit emotion truth claims |
| MediaPipe | video metadata | Pose, face mesh, and landmark metadata for rights-cleared windows | No identity, surveillance, or body-language truth claims |
| OpenFace | video metadata | Action-unit and head-pose metadata | No biometric identity inference |
| MMPose | video metadata | Pose landmark metadata | Observable cues only |
| BYOK reviewer layer | text/multimodal metadata | Reviewer synthesis over fixed evidence bundles | reviewer-support only, not canonical |

## Dataset radar with rights caveats

External datasets are benchmark-only by default until a separate license and rights review is documented. They cannot become Signal Engine gold labels. Gold labels remain human-adjudicated only.

| Dataset/resource | Modality | Research relevance | Rights and safety caveat |
| --- | --- | --- | --- |
| CMU-MOSEI | multimodal | Sentiment and affective language research | External benchmark only; check license and redistribution limits |
| CMU-MOSI | multimodal | Small multimodal sentiment benchmark | External benchmark only; no production claim |
| IEMOCAP | audio/video/text | Emotion corpus reference | License review required; not emotion truth |
| MELD | text/audio/video | Dialogue affect research | External benchmark only; media rights must be checked |
| MSP-Podcast | audio | Speech affect research | License and consent constraints must be reviewed |
| DAIC-WOZ | audio/video/text | Health-context caution example | Health/sensitive caution only; excluded from Signal Engine product use |
| GoEmotions | text | Text-label taxonomy reference | Benchmark only; labels are annotator judgments, not truth |
| rights-cleared/manual-local earnings-call audio/video placeholder | audio/video metadata | Possible future selective audit | Requires manual-local source record, consent/source rights, and rights-cleared storage rules |

## Legal and ethical guardrails

- Require rights-cleared source records before any media metadata extraction.
- Require explicit consent/source-rights notes for manual-local media.
- Keep raw media out of commits and default storage.
- Keep audit to flagged windows only; no full-call brute-force multimodal processing.
- Store cue metadata, confidence, extractor version, and provenance instead of raw audio/video.
- Do not use this layer for employment, education, access-control, credit, insurance, healthcare, deception, or mental-health use cases.
- Do not infer protected or sensitive traits.
- Do not treat external dataset labels as canonical truth or Signal Engine gold labels.

## Failure modes

- ASR or diarization errors can make pauses, overlaps, and interruptions inaccurate.
- Video angle, lighting, compression, and camera framing can distort metadata.
- Cultural, disability, neurodiversity, accent, language, and role differences can make cue interpretation unsafe.
- Finance calls have scripted remarks, legal disclaimers, and analyst dynamics that can mimic pressure or uncertainty.
- Reviewer anchoring can occur if metadata is presented as an emotion label.
- External benchmark labels may not transfer to earnings-call settings.
- Provider outputs can add unsupported language unless constrained by fixed schemas and red-line checks.

## Safe output schema

Safe records should include only:

- record_id
- source_type: transcript, audio_metadata, video_metadata, or multimodal_audit
- canonical_status: reviewer_support_only
- transcript_window_ref
- feature_name
- feature_value or feature_summary
- confidence or extractor confidence
- provenance
- interpretation_limits:
  - does_not_infer_true_emotion
  - does_not_detect_deception
  - does_not_score_personality
  - not_canonical_signal

Safe records must not include raw_text, raw_audio, raw_video, emotion_label, deception_score, manipulation_score, mental_health_label, biometric_identity, sensitive_trait_inference, trading_signal, or relationship_manipulation_score.

## What not to build

- No raw audio/video ingestion pipeline.
- No YouTube scraping or media download.
- No external dataset ingestion.
- No model training code.
- No production emotion-recognition model.
- No deception detection.
- No mental-health diagnosis.
- No biometric identity inference.
- No workplace/education emotion inference.
- No relationship manipulation scoring.
- No full-call brute-force multimodal processing.
- No outputs that override deterministic transcript extraction.

## Evaluation plan

1. Start with transcript-only deterministic signals and human-reviewed evidence spans.
2. Select only flagged windows where deterministic transcript cues already justify review.
3. Verify rights-cleared source status before any audio/video metadata is produced.
4. Generate allowed metadata fields only, with extractor confidence and provenance.
5. Run reviewer studies that ask whether metadata improves evidence review usefulness, not whether it detects emotion.
6. Track macro F1, calibration/ECE, abstain rate, reviewer usefulness, invalid citation rate, and unsupported claim rate.
7. Fail closed if reviewers report anchoring, unsupported affective language, or any pressure to treat metadata as canonical.
