# Adjudication Workflow

Reviewer packets contain machine candidates only. They are not gold labels.

Promotion requires:

- `review_status=adjudicated`
- `adjudicator`
- `adjudicated_at`
- final label and final evidence text
- final source file and provenance hash
- reviewer rationale
- no unresolved contamination flags
- no external dataset source
- no weak-label-only source
- no duplicate provenance hash

Use `data/review/templates/adjudication_template.json` for staged adjudication records.
