# Label Review Fast Pass Guide

Use this guide for the next quick manual pass over [`data/nlp_research/candidate_review_priority_30.csv`](../data/nlp_research/candidate_review_priority_30.csv).

## Allowed Labels

- `risk_friction`
- `opportunity_commitment`
- `uncertainty_hedging`
- `neutral`

## How To Review The 30-Row Packet

1. Read the full `text` cell first.
2. Ignore the suggested label until you have your own first impression.
3. Use `suggested_evidence_terms` and `priority_reason` only as a check, not as truth.
4. Fill:
   - `reviewer_label`
   - `reviewer_confidence`
   - `reviewer_notes`
   - `accepted`
5. Mark `accepted=yes` only when the text is safe, readable, and clearly fits one label better than the others.

## When To Reject A Candidate

Reject or leave `accepted` blank when:

- the text is too truncated to judge safely
- the text is really documentation or report language rather than conversation content
- the snippet still contains placeholder-heavy contact details that make it low-value for training
- the text is too ambiguous to trust as a standalone training example
- the text duplicates a stronger row already in the packet

## When To Mark `accepted=yes`

Mark `accepted=yes` when all of these are true:

- the snippet is understandable on its own
- the reviewer label is clear enough to defend in one sentence
- the snippet does not rely on hidden context or unsupported inference
- the row would improve the reviewed dataset if added

## Handling Ambiguity

- If a row reads like a complaint, blocker, or escalation, prefer `risk_friction`.
- If a row reads like a concrete follow-up, ownership statement, or dated action, prefer `opportunity_commitment`.
- If a row is mainly conditional, hedged, or visibility-limited, prefer `uncertainty_hedging`.
- Use `neutral` only for operational or logistical language with no stronger friction, commitment, or hedge signal.
- If two labels both seem plausible, pick the safer less-strong label and explain the ambiguity in `reviewer_notes`.

## Target Distribution For The Next 30 Accepted Labels

If enough good rows exist, aim for:

- `8` neutral
- `8` risk_friction
- `7` uncertainty_hedging
- `7` opportunity_commitment

Current caution:

- the mined pool is rich in friction and commitment rows
- the clean `neutral` and `uncertainty_hedging` pool is thinner and noisier
- do not force weak hedge or neutral rows just to hit a target mix

## Rerun Commands After Editing

```bash
make data-growth-refresh
make best-in-class-refresh
```
