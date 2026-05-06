# Portfolio Demo Report

Signal Engine 2.0 is a transcript-first evaluation workflow for turning messy business communication into evidence-backed signal candidates, review packets, and benchmark reports.

## What The Demo Shows

- Public transcript/source intake is kept separate from label promotion.
- Provenance is preserved before analysis.
- Deterministic extraction produces reviewable candidate signals.
- Weak labels remain suggestions until a human reviewer accepts them.
- Evaluation reports compare deterministic output against reviewed labels.
- ML and retrieval stay benchmark/support layers.

## Current Metrics

- gold labels: `57`
- deterministic metrics: precision `0.8399`, recall `0.8326`, F1 `0.8276`
- human-reviewed-only F1: `0.5794`
- fixture-excluded F1: `0.646`
- TF-IDF/logistic-regression F1: `0.7327`
- retrieval status: `skipped`

These are small-benchmark metrics for workflow evaluation, not statistical proof or production ML performance.

## Review Boundary

No transcripts or gold labels are auto-promoted by this demo. Human review remains the gate for accepted labels.
