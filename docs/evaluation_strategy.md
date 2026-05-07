# Evaluation Strategy

Signal Engine 2.0 keeps the evaluation path simple: deterministic transcript-first outputs are measured against reviewed labels, while ML and retrieval remain support layers.

## Deterministic baseline

The deterministic extractor is the canonical system. It produces evidence-backed candidates and is evaluated against the current gold-label file.

Latest committed all-label metrics:

- precision `0.8399`
- recall `0.8326`
- F1 `0.8276`
- gold labels `57`

These are small-benchmark metrics, not statistical proof.

## Reviewed gold labels

Gold labels are accepted review outcomes. They should include source text, label, and enough context to trace the decision. Weak labels do not become gold labels unless a human reviewer accepts them.

## Weak labels are only suggestions

Weak-label candidates help reviewers move faster. They are not evaluation truth and are not auto-promoted.

## Human-reviewed metrics

The current human-reviewed-only subset is small:

- rows `12`
- precision `0.6`
- recall `0.6375`
- F1 `0.5794`

This is the more conservative lens for product claims until the reviewed set grows.

## Fixture-excluded metrics

The fixture-excluded subset helps show how much fixture-like data influences the headline metric:

- rows `21`
- precision `0.6429`
- recall `0.6833`
- F1 `0.646`

## ML baseline

The TF-IDF/logistic-regression baseline is benchmark-only:

- precision `0.7332`
- recall `0.7328`
- F1 `0.7327`

It does not replace deterministic transcript-first output.

## Retrieval benchmark gate

Retrieval is scaffolded and gated. Current committed reports show retrieval skipped because the repo has fewer than 100 labels unless explicit retrieval experiment mode is enabled.

## Why more labels are needed

The current benchmark is useful for workflow validation and regression checks. It is not large enough for strong claims about statistical significance, model generalization, or production performance.

## Next target

The near-term target is a 100-call corpus and 500-1,000 reviewed labels. That would make subset metrics, model comparison, and retrieval evaluation more meaningful.
