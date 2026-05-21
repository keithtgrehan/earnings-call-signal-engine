# Evaluation Claims Matrix

The claims matrix keeps product language aligned with evidence.

Use `configs/claims_matrix.example.yml` and validate with:

```bash
python scripts/validate_claims_matrix.py --path configs/claims_matrix.example.yml
```

## Supported

- deterministic transcript extraction produces reviewable signal candidates;
- evidence spans and provenance are preserved in reviewed workflows;
- human-reviewed labels are required for gold/evaluation claims.

## Gated

- retrieval quality claims require a fixed retrieval benchmark, reviewed-label volume, and provenance preservation;
- fine-tuning claims require enough reviewed labels, held-out evaluation, source rights, and comparison against deterministic and retrieval baselines;
- event-study packaging can support case context, but not alpha or trading claims.

## Not Supported

- live trading or execution;
- investment advice;
- alpha claims;
- statistical-significance claims without sufficient data;
- production ML claims;
- claims based on weak labels, external benchmark rows, or restricted source bodies.

Unsupported claims must be marked `not_supported`, not softened into roadmap language.
