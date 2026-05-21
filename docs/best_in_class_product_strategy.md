# Best-in-Class Product Strategy

Signal Engine should win on trust, provenance, and reviewability, not on unsupported alpha claims.

## Built

- transcript-first deterministic extraction;
- evidence spans and provenance-backed case workflows;
- weak-label candidate generation;
- human-review and promotion paths;
- small but useful deterministic and ML benchmark reports;
- no-trading and no-statistical-significance guardrails.

## Scaffolded in This Rollout

- resource registry schema and starter config;
- source license records and corpus case rights fields;
- metadata-only adapters for SEC EDGAR, company IR, FRED-like macro sources, and manual local sources;
- restricted-artifact checker;
- separated training-candidate export buckets;
- claims matrix validator;
- corpus/resource dashboard.

## Gated

- raw transcript storage from official IR pages until terms are checked;
- external dataset benchmarking until local files and rights are verified;
- retrieval/embedding evaluation until reviewed-label gates are met or explicit experiment mode is used;
- fine-tuning until reviewed-label quality, sample size, held-out evaluation, and rights checks are strong enough.

## Planned

- grow legally usable transcript cases with source-level provenance;
- scale human-reviewed labels;
- add retrieval over evidence objects before model training;
- improve error analysis and false-positive controls;
- use event-study case packaging only as contextual research, not trading proof.

## Explicitly Not Supported

- live trading, execution, or investment advice;
- alpha claims;
- statistical-significance claims without sufficient reviewed data;
- broad scraping, paywall/login bypassing, or robots violations;
- committing restricted transcript/audio/video bodies;
- automatic promotion of weak labels or external dataset rows into gold.
