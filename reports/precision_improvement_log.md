# Precision Improvement Log

## Accepted Refinements

- Added conditional-language suppression for generic opportunity terms.
- Added status-context suppression for generic risk terms.
- Added guidance/outlook detectors for raised, flat, down, and forward-looking guidance.
- Added explicit explainability fields: `score_by_label`, `confidence`, `suppressed_terms`, `rule_version`.

## Rejected Refinements

- No broad architecture rewrite attempted.
- No ML or retrieval replacement for deterministic output attempted.
- No label edits or synthetic labels created.

## Metric Delta

- precision_delta: `0.5194`
- recall_delta: `0.3827`
- F1_delta: `0.4533`

Acceptance rules were satisfied on all-label metrics. Because the dataset is small, source-quality subset reports remain mandatory context.
