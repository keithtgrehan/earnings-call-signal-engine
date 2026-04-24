# Signal Engine 2.0

Signal Engine 2.0 is the forward product branch for deterministic, explainable conversation intelligence across support, sales, account management, and earnings-call workflows.

## Product Vision

Signal Engine 2.0 extends the repository from a support-QA MVP into a broader conversation intelligence layer that can score transcript-like conversations offline with evidence-backed outputs and no required external APIs.

Core positioning:

- deterministic, explainable conversation intelligence
- support, sales, and account management first
- earnings calls preserved as a reference vertical
- transcript-first and offline by default
- optional multimodal enrichments only where useful and safe

## Supported Domains

| Domain | Primary users | Examples of deterministic signals |
| --- | --- | --- |
| Support conversation | QA, support ops, escalation review | directness, deflection, frustration, resolution clarity, escalation risk |
| Sales call | sales managers, revenue ops | buyer intent, objections, pricing concerns, next-step clarity, competitor mentions, rep overtalk proxy |
| Account management call | CS leaders, renewals, account teams | churn risk, renewal risk, expansion opportunity, unresolved issues, sentiment proxy, commitment clarity |
| Earnings call | analysts, portfolio research, audit trail | analyst pressure, caution language, answer deflection, confidence language, follow-up commitments |

## Deterministic Core

Built-now canonical scoring uses:

- transcript text and role/turn structure
- lexicons and regex rules
- simple counts, ratios, and prompt-response structure
- evidence rows tied to specific transcript segments

The canonical path does not require:

- LLM calls
- external APIs
- cloud services
- model downloads
- UI infrastructure

## Optional Multimodal Enrichments

Signal Engine 2.0 is text-first. Audio and video enrichments are future-ready but not required for canonical scoring.

Optional paths include:

- offline ASR when only audio is available
- diarization to improve speaker-role mapping
- audio prosody and pause features for review workflows
- video keyframes for flagged moments only
- local retrieval experiments for analyst review, not canonical truth

## Built Now

- `src/signal_engine/` package with unified schemas and deterministic domain scoring
- support, sales, account-management, and earnings-call domain scaffolding
- transcript-first offline CLI
- tiny sample JSON inputs
- focused tests for repeatability, schema shape, evidence presence, and zero-API execution
- preserved legacy support-QA MVP and preserved earnings-call assets in git history

## Roadmap

- optional ASR adapters such as faster-whisper or WhisperX
- optional diarization via pyannote.audio
- optional audio features from librosa, torchaudio, or openSMILE
- optional video keyframes via OpenCV, PySceneDetect, and ffmpeg
- optional local retrieval and semantic review layers
- optional long-context review workflows separate from canonical scoring

## No-Hype Constraints

- deterministic core first
- evidence-backed outputs only
- transcript path must work offline
- no LLM dependency in canonical scoring
- no external APIs required
- no large datasets added
- no downloaded model artifacts committed
- no broad destructive refactor
- built-now scope must remain separate from roadmap

## Relationship To Existing Work

The existing support-QA MVP and the historical earnings-call workflow remain in the repository. Signal Engine 2.0 is additive: it broadens the product direction without deleting earlier work or treating optional multimodal components as required runtime dependencies.
