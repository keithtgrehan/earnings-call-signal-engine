# Gold Label Schema

Gold labels are human-adjudicated records only. Machine suggestions, weak labels, external benchmark rows, retrieval hits, and BYOK reviewer outputs cannot become gold without an explicit reviewed promotion manifest.

Required fields for the first audit gate:

- `case_id`
- `label_id`
- `signal_type`
- `direction`
- `speaker_role`
- `evidence_text`
- `reviewer`
- `reviewed_at`
- `source_file`
- `provenance_hash`

The audit scripts are read-only against `data/gold/gold_labels.jsonl`. Repair candidates are written to `reports/gold_label_audit/` and review staging, never back into canonical gold.

Blocked classes:

- external dataset rows
- weak-label-only rows
- duplicate `label_id`
- missing provenance
- unresolved contamination flags
- machine suggestions without human final labels
