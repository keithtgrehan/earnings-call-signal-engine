# Model Registry

The model registry is a planning and audit surface. Tracked does not mean implemented, production-ready, or validated.

## What Is Real Now

- `deterministic_rules_baseline` is the current deterministic baseline family.
- `weak_label_keyword_baseline` is a deterministic keyword/rule scaffold for reviewable weak labels.
- Both are deterministic baselines, not trained ML.

## What Is Candidate Or Planned

- `local_sklearn_text_classifier` is optional local smoke scaffolding only.
- `sentence_transformers_local_candidate` would require a local model download later.
- OpenAI, Voyage, Cohere, Jina, Anthropic, and Google entries are future benchmark candidates only.
- No paid/API outputs are required for the current scaffold.
- No model weights are committed.

## Guardrails

- Registry presence is not evidence of model quality.
- Candidate models must not be advertised as implemented.
- Smoke tests must not be presented as validated ML.
- Validated ML requires held-out labelled data, repeatable metrics, and documented error analysis.
