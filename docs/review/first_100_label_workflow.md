# First-100 Label Workflow

The next proof path is to repair or adjudicate the first 100 transcript-backed labels before any real training claim.

Workflow:

1. Run `make gold-audit`.
2. Run `make first-100-review-queue`.
3. Human reviewers adjudicate staged candidates outside the canonical gold file.
4. Create `data/review/staging/promotion_manifest.jsonl` only for reviewed/adjudicated rows.
5. Run `make promotion-manifest-check`.
6. Promote to canonical gold only through a separate explicit promotion task.

Guardrails:

- candidate rows use `gold_status=not_gold`
- review rows use `review_status=pending_human_review` until adjudicated
- machine suggestions remain metadata only
- external and weak-label rows cannot be promotion candidates
- unresolved contamination flags block promotion
- no raw transcript/audio/video body is copied into review staging by this workflow
