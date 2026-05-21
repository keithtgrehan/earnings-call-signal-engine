# Data Rights and Corpus Policy

Signal Engine is transcript-first, evidence-backed, and rights-cleared by default. A source is usable only when its rights tier, provenance, storage permissions, and evaluation/training permissions are recorded.

## Rights Tiers

- `public_domain`: government or public-domain material. Still preserve attribution, source URL, access date, and fair-access notes.
- `publicly_available`: visible on the web but not automatically reusable. Treat as metadata-only until terms are checked.
- `official_public_terms_checked`: official company or source-hosted material with robots/site terms checked.
- `open_licensed`: license permits stated reuse. Record exact license, version, attribution, and redistribution/training limits.
- `licensed`: use is governed by a contract or explicit permission. Commit/training/evaluation permissions must be explicit.
- `manual_supplied`: supplied by an operator or user. Requires source URL/path, attestation, license notes, and provenance.
- `restricted`: paywalled, login-gated, subscription, vendor, blocked, or unclear-rights material. Raw bodies are blocked.

## Allowed Use

Resource registry rows must declare `allowed_storage`, `allowed_commit`, `allowed_training_use`, `allowed_eval_use`, `raw_body_allowed`, and `metadata_only`.

| Tier | Default storage | Default commit | Training use | Evaluation use |
| --- | --- | --- | --- | --- |
| `public_domain` | metadata; raw only if source rules allow | metadata allowed | no by default | benchmark/context allowed |
| `publicly_available` | metadata-only | metadata only | no | no or benchmark-only after review |
| `official_public_terms_checked` | metadata; raw only after terms allow | metadata by default | review required | review required |
| `open_licensed` | per license | per license | per license | per license |
| `licensed` | per contract | only if explicit | only if explicit | only if explicit |
| `manual_supplied` | local/manual until attested | only if explicit | review required | review required |
| `restricted` | blocked or metadata-only blocked reference | no raw commit | no | no |

Default posture:

- metadata is allowed only when source terms allow it and provenance is preserved;
- raw transcript/audio/video bodies are blocked unless the rights record explicitly allows storage;
- raw restricted transcript-provider bodies must not be copied, committed, trained on, or used as evaluation truth;
- external datasets can support benchmarks or adapters, but cannot become Signal Engine gold labels;
- weak labels remain candidates until a human reviewer accepts them.

## Official and Government Sources

SEC EDGAR/companyfacts should be used through official SEC APIs and developer guidance, including fair-access behavior and a descriptive user agent. The starter adapter is metadata-only and performs no live downloads by default. See official SEC API entry points at `https://data.sec.gov/` and SEC EDGAR API documentation.

Company investor-relations pages are preferred when terms allow transcript use, but each company page still needs a robots/site terms check. Public availability is not enough.

FRED and macro sources require series-level terms checks. FRED API terms note that source-owner rights and restrictions can still apply to individual series, so Signal Engine records macro sources as metadata/context until terms are confirmed.

## Commit Rules

Run `python scripts/check_restricted_artifacts.py --staged` before committing corpus changes. Raw transcripts, audio, video, provider text, and generated label packets should stay out of commits unless a registry record explicitly allows raw-body commit and provenance.

## Gold and Evaluation

Gold labels require human review. External rows and weak labels are never auto-promoted. Evaluation claims must cite the reviewed-label set and state limitations when sample size is small.
