# Transcript Sectioning And Labeling Playbook

This playbook defines the manual review workflow for the first three earnings-call corpus cases. It is not a transcript source and does not validate any model.

## Intake Order

1. Confirm the official investor-relations source.
2. Confirm transcript reuse rights manually.
3. Store permitted local transcript text outside git or in the approved case path only if explicitly approved.
4. Section the transcript into prepared remarks, Q&A, and unknown.
5. Validate speaker names and roles.
6. Add manual labels with short evidence spans.
7. Review labels and promote only when source, sectioning, speakers, and evidence are defensible.

## Sectioning Rules

- Prepared remarks include scripted management commentary before analyst Q&A.
- Q&A starts when the operator opens questions or analyst turns begin.
- Operator and safe-harbor language should be preserved but not treated as management guidance.
- Use `unknown` when boundaries are ambiguous.
- Do not delete turns that complicate the case; flag them for review.

## Speaker Validation Rules

- Use `management`, `analyst`, `operator`, or `unknown`.
- Preserve original speaker names when available.
- Do not infer an analyst or management role from content alone.
- Mark ambiguous or missing speakers as blockers until reviewed.

## Labeling Expectations

- Use the schema shape in `data/gold_labels.example.jsonl`.
- Manual labels should include `case_id`, `signal_type`, `direction`, `speaker_role`, `evidence_text`, confidence, notes, and reviewer metadata when a real label file is created.
- Weak labels are review aids only and must not be promoted as gold labels.

## Evidence Span Requirements

- Evidence must be short enough to audit and long enough to justify the label.
- Guidance labels need an explicit outlook, forecast, range, reaffirmation, withdrawal, or comparable management language.
- Q&A friction labels should include the analyst question and relevant management answer when possible.
- Generic optimism, generic uncertainty, or isolated keywords are not enough.

## Promotion Pipeline

`source-confirmed -> transcript-ready -> sectioned -> labeled -> reviewed`

Promotion requires manual confirmation at every step. A case should remain blocked if source rights, transcript quality, section boundaries, speaker roles, or evidence spans are uncertain.
