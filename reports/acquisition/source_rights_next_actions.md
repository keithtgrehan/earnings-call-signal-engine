# Source Rights Next Actions

- Queue fields added for next approval pass: `candidate_id`, `case_id`, `transcript_rights_status`, `audio_rights_status`, `transcript_download_allowed`, `audio_download_allowed`, `license_config_ref`, `approval_notes`, `approved_by`, `approved_at`.
- VZ 2024 Q4 transcript and direct MP3 are approval-gated until source terms review is complete.
- HD 2025 Q4 webcast remains metadata-only because the ChorusCall URL is a player page, not a direct audio file.
- Unknown rights fail closed.
- Vendor raw requires `license_config_ref`.
- `commit_allowed=false` for all raw assets.
- `training_allowed=false` unless explicit training rights are present.

## Manual Actions
- Review Verizon official direct transcript PDFs and MP3 source terms.
- Confirm whether Verizon MP3 is prepared-only or full-call audio before marking pair verified.
- Add `approved_by` and `approved_at` only after source-rights review.
