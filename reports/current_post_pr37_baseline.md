# Current Post-PR37 Baseline

- PR #36 merged.
- PR #37 merged.
- PR #38 merged after PR #37 and is included in the clean `main` baseline.

## Current Capabilities

- Transcript-first deterministic extraction scaffolds exist.
- Rights-gated Agent 5 metadata queues exist for NYSE pilot/source discovery.
- Human review workflow scaffolds exist for first-100 review and promotion validation.
- Training readiness reports exist and do not train models.

## Current Blockers

- Raw transcript/audio/video/slides ownership is not assumed.
- Manual-local transcript registry can be empty.
- Canonical legacy rows present: `57`.
- Strict gold-valid count: `0` in the current audit because rows are blocked on sha256 provenance.
- First-100 ranked review queue: `48` machine candidates.
- Agent 1 candidate count from registered manual-local sources: `0` until transcript paths are registered.
- Retrieval and event-study layers are readiness scaffolds, not benchmark proof.

## Training Readiness

Training remains `NOT_READY` until staged promoted labels pass validation and valid adjudicated count is at least 100.

## Next Manual Actions

- Register rights-cleared transcript paths by path/hash only.
- Review calibration and first-100 packets.
- Keep vendor/YouTube raw ingest blocked unless explicit config is approved.
