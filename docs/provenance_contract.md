# Provenance Contract

Every candidate or promoted label must preserve:

- `case_id`
- `source_file`
- `source_sha256`
- `evidence_span_ref`
- `provenance_hash`
- `text_hash` or redacted preview hash where raw text cannot be committed
- `rule_id`
- `rule_version`
- `created_at`

Manual-local files are registered by path and sha256 hash only. Raw files are not copied into the repository.

Gold promotion requires human adjudication, `adjudicator`, `adjudicated_at`, final evidence/source fields, a reviewer rationale, and no unresolved contamination flags.
