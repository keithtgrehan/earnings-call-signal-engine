# First100 Adjudication Workflow

This workflow converts metadata-only machine candidates into human-reviewed promotion candidates. It does not promote labels to gold and does not authorize model training.

1. Review the first100 packet markdown files and source material under the approved Desktop corpus workspace.
2. Fill an adjudication JSONL row for each accepted or rejected candidate using `data/review/templates/first100_adjudication_template.json`.
3. Keep `suggested_label` as machine context only. Set `final_label`, `reviewer`, `rationale`, `adjudicator`, and `adjudicated_at` independently.
4. Do not copy raw transcript text into repo files. Keep evidence references as source paths, hashes, evidence object IDs, chunk IDs, and provenance hashes.
5. Run `python3 tools/validate_first100_promotion_manifest.py` before any promotion workflow.
6. Treat training as blocked until at least 100 valid adjudicated labels exist, provenance is complete, promotion gates pass, and explicit training rights are configured.

Current expected state is `REVIEW_READY` when at least 100 pending candidates and packets exist. Training remains `NOT_READY`.
