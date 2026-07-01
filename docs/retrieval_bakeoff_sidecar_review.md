# Retrieval Bakeoff Sidecar Review

Status: `retrieval_bakeoff_plan_only`.

## Experiment Design Findings

- Use existing retrieval metric vocabulary only: recall@1/3/5, MRR, exact evidence ID hit rate, citation validity, invalid citation, wrong case/ticker/period, abstention correctness, fallback overuse, latency summaries, and provenance completeness.
- The HD query file is smoke-only and cannot support real benchmark status.
- Real benchmark planning requires reviewed query rows with concrete evidence IDs and no placeholders.
- The plan report must list metrics as planned only and must not imply provider ranking or provider performance.

## Artifact Safety Findings

- Bakeoff planning must validate retrieval object metadata before provider planning.
- Output roots must avoid committed repo paths and restricted artifact components.
- Reports may include metadata digests and counts only.
- Raw transcript text, ASR/audio text, chunk text, provider responses, embeddings, vector stores, labels, adjudication rows, training data, and promotion rows remain blocked.

## Developer Usability Findings

- The default command sequence is documented in `docs/retrieval_bakeoff_process.md`.
- The provider enablement path is documented in `docs/retrieval_provider_enablement_playbook.md`.
- Current example manifest uses only `local_stub`, `network_allowed=false`, and smoke-only query status.

## Remaining Blockers Before Real Benchmark

- Reviewed retrieval eval query set is not present.
- Reviewer approval is not recorded.
- Real provider config must remain non-committed until explicitly approved.
- Generated provider artifacts must remain local-only and be cleaned before commit.
- Current output supports scaffold readiness only, not retrieval quality or production RAG claims.
