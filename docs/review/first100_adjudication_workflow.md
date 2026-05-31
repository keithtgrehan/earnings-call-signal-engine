# First100 Adjudication Workflow

This workflow turns metadata-only machine candidates into human adjudication drafts. It does not promote labels to gold and does not authorize model training.

## Inputs

- Candidate file: `data/review/staging/first100_signal_candidates.jsonl`
- Review packets: `data/review/packets/first100_batch_*.md`
- Adjudication template: `data/review/templates/first100_adjudication_template.json`
- Approved source material: Desktop corpus workspace only

## Fill One JSONL Row Per Reviewed Candidate

Copy identifiers and hashes from the packet exactly. Do not paste transcript text, quotes, snippets, audio text, or source excerpts into the JSONL.

Required reviewer-entered fields:

- `candidate_id`: exact candidate id from the packet.
- `adjudicated_label`: one of `guidance_revision`, `guidance_statement`, `analyst_pressure`, `management_hedging`, `uncertainty`, `reassurance`, `answer_shift`, `neutral/no_signal`, `reject_candidate`, `needs_source_review`, or `needs_adjudication`.
- `reviewer`: stable reviewer id with at least 3 letters/numbers.
- `rationale`: short reason for the decision, without raw transcript text.
- `review_status`: `adjudicated`.
- `gold_status`: `not_gold`.
- `promotion_decision`: `not_requested`.

Required provenance fields:

- `source_file`
- `source_sha256`
- `normalized_transcript_hash`
- `text_hash`
- `provenance_hash`
- `evidence_object_id` or `chunk_id`

Training and promotion fields must remain blocked:

- `training_export_requested=false`
- `training_allowed=false`
- `explicit_training_rights_ref=""`
- no `final_evidence_text`
- no `gold_status=promotion_candidate`

## Placeholder Example

This example uses fake ids only. Do not copy it as a real adjudication row.

```json
{"candidate_id":"fake_candidate_001","case_id":"fake_2025_q4","ticker":"FAKE","fiscal_period":"2025 Q4","suggested_label":"MACHINE CANDIDATE ONLY","adjudicated_label":"needs_source_review","review_status":"adjudicated","gold_status":"not_gold","reviewer":"reviewer_1","rationale":"Metadata reviewed; source needs a second pass.","source_file":"/Users/keith/Desktop/earnings calls 100 samples/fake/source.txt","source_sha256":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","normalized_transcript_hash":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","text_hash":"sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","provenance_hash":"sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","evidence_object_id":"fake_evidence_id","chunk_id":"fake_chunk_id","unresolved_contamination_flags":[],"weak_label_only":false,"promotion_decision":"not_requested","training_export_requested":false,"training_allowed":false,"explicit_training_rights_ref":""}
```

## Dry-Run Command Sequence

Use a local path for the draft adjudication JSONL until it is ready to commit as a metadata-only review artifact.

```bash
python3 tools/validate_first100_adjudication_file.py --adjudication /path/to/first100_adjudication_draft.jsonl
python3 tools/validate_first100_promotion_manifest.py --manifest data/review/staging/first100_promotion_manifest.jsonl
python3 tools/report_first100_training_readiness.py
python3 tools/build_review_readiness_dashboard.py
```

Expected current status before human review:

- `adjudicated_rows=0`
- `promotion_manifest_status=NOT_READY`
- `training_ready=false`
- `explicit_training_rights=false`

Training remains blocked until at least 100 valid adjudicated labels exist, provenance is complete, promotion gates pass, and explicit training rights are configured.
