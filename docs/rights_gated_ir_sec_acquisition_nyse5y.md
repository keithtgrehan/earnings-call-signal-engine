# Rights-Gated IR/SEC Acquisition for NYSE 5-Year Discovery

## 1. Goal

Design a metadata-first, rights-gated discovery and permitted acquisition workflow for NYSE earnings-call-related materials from the past 5 years using official company Investor Relations sources and SEC/EDGAR metadata/exhibit references.

The tool should identify as much as possible while failing closed for raw content. Raw transcript, audio, video, slide, vendor, and platform media use requires explicit source-rights config, checked terms/robots where applicable, and approval or license references.

## 2. Scope

- Exchange: NYSE only.
- Time range: rolling past 5 years, represented as fiscal-period placeholders until exact event dates are verified.
- Seed universe: existing 30 NYSE pilot tickers.
- Network mode: disabled by default.
- Default mode: metadata only.
- Raw content acquisition: disabled by default.

## 3. Source Hierarchy

1. `official_ir_metadata`: official company IR section candidates, metadata only until terms/robots review is complete.
2. `official_ir_permitted_raw`: official IR raw acquisition candidate only after explicit permission, checked terms/robots, allowed storage flags, and approval reference.
3. `sec_edgar_metadata`: SEC company submissions and extracted metadata references, metadata first.
4. `sec_exhibit_metadata`: SEC exhibit references and exhibit metadata, without filing body downloads by default.
5. `manual_local`: operator-supplied local path plus sha256 hash only; no file copying by default.
6. `blocked_restricted`: paywall/login/vendor/platform/unknown-rights candidates that remain blocked for raw use.

## 4. What This Can Collect

- event identity targets
- call dates or fiscal-period placeholders
- earnings release references
- 8-K, 10-Q, and 10-K references
- exhibit metadata references
- official IR candidate URL/reference placeholders
- transcript/audio/video/slides availability indicators
- manual-action queue entries
- blocked reason codes
- provenance hashes for metadata rows

## 5. What It Must Not Collect by Default

- raw transcript bodies
- raw audio/video
- slide PDFs
- vendor transcripts
- YouTube media
- filing body text
- login-gated or paywalled content

## 6. What Is Missing Versus Manual-Local Method

Manual-local registration can provide:

- guaranteed transcript body access when the operator already controls the file
- already reviewed source-rights context
- manually verified transcript quality
- direct local file hash
- human-confirmed provenance
- local permission context

IR/SEC metadata discovery cannot guarantee any of those. It can identify likely source candidates and filing context, but the raw transcript body remains unavailable until a rights-cleared source or manual-local path/hash is registered.

## 7. Rights Decision Tree

1. If source rights are unknown and raw use is requested, block with `unknown_rights`.
2. If source requires paywall/login access, block with `paywall_or_login_required`.
3. If vendor raw use is requested without `license_config_ref`, block with `licensed_vendor_without_license_config`.
4. If YouTube raw media is requested without explicit authorization, block with `youtube_raw_media_blocked_without_authorization`.
5. If SEC raw filing bodies are requested, block with `sec_metadata_only`.
6. If official IR raw use lacks checked source terms, block with `source_terms_not_checked`.
7. If official IR raw use lacks robots review where required, block with `robots_not_checked`.
8. If raw ingest flags are disabled by policy, block with `raw_ingest_disabled_by_policy`.
9. If raw commit is requested while commit policy is false, block with `raw_commit_forbidden`.
10. If training use lacks explicit approval, block with `training_use_forbidden`.
11. If provenance is incomplete, block with `provenance_incomplete`.
12. Otherwise, metadata-only rows remain allowed as metadata-only; permitted raw rows enter only the permitted ingest queue.

## 8. SEC Fair-Access Policy

SEC/EDGAR use is metadata first. The SEC supports company submissions and extracted XBRL/companyfacts-style data through official data endpoints, but the workflow does not assume full earnings-call transcript availability.

Fair-access rules:

- maximum request rate: 10 requests/second
- descriptive User-Agent required before any future network-enabled metadata fetch
- cache directory configurable
- network disabled by default
- filing body downloads disabled by default
- tests remain network-free

SEC is useful for event timing, 8-K references, earnings releases, periodic filing context, and exhibit metadata. It is not a guaranteed transcript source.

## 9. Official IR Terms/Robots Policy

Official IR is the preferred transcript source when terms allow. Company pages vary by source terms, robots rules, and hosting practices, so raw acquisition requires source-specific review.

Default posture:

- official IR candidate mapping is metadata only
- raw body use disabled
- source terms check required
- robots check required
- manual approval required for raw acquisition
- storage, commit, evaluation, and training flags must be explicit

## 10. Manual-Local Fallback Workflow

When source terms are unclear, use manual-local registration:

1. Operator supplies a local file path.
2. Tool records path and sha256 hash.
3. Tool does not copy the raw file into the repo.
4. Operator records source-rights notes outside the raw acquisition path.
5. Downstream parsing reads only from the approved local path.

This remains the fastest fully controlled path when source terms are unclear.

## 11. Failure Modes

- unknown rights: raw use blocked
- missing source terms check: official IR raw use blocked
- missing robots check: official IR raw use blocked where required
- paywall/login required: raw use blocked
- vendor raw use without license config: blocked
- YouTube raw media without authorization: blocked
- SEC request rate above 10 requests/second: policy invalid
- SEC User-Agent missing when enabled: policy invalid
- raw filing body downloads enabled: policy invalid
- provenance hash missing: candidate invalid
- blocked candidate missing manual action: candidate invalid

## 12. Validation and Report Outputs

Configs:

- `configs/ir_sec_acquisition_policy.example.yml`
- `configs/nyse_5y_ir_sec_targets.example.yml`

Schemas:

- `schemas/ir_sec_acquisition_policy.schema.json`
- `schemas/ir_sec_source_candidate.schema.json`
- `schemas/ir_sec_event_identity.schema.json`
- `schemas/ir_sec_asset_availability.schema.json`
- `schemas/ir_sec_permitted_ingest.schema.json`

Metadata outputs:

- `data/corpus/nyse_5y_ir_sec_universe.yml`
- `data/corpus/official_ir_candidate_map.yml`
- `data/corpus/sec_metadata_queue.yml`
- `data/corpus/ir_sec_permitted_ingest_queue.yml`

Reports:

- `reports/agent5/nyse_5y_ir_sec_universe.md`
- `reports/agent5/official_ir_candidate_map.md`
- `reports/agent5/sec_metadata_queue.md`
- `reports/agent5/ir_sec_availability_matrix.csv`
- `reports/agent5/ir_sec_availability_matrix.md`
- `reports/agent5/ir_sec_permitted_ingest_queue.md`
- `reports/agent5/manual_local_vs_ir_sec_gap.md`

Validation commands:

- `make validate-ir-sec-acquisition-policy`
- `make validate-ir-sec-source-candidates`
- `make validate-ir-sec-availability-matrix`
- `make validate-ir-sec-permitted-ingest`
- `make ir-sec-acquisition-check`
