# Canonical Review Schema

The canonical review object is the contract between deterministic signal extraction, Argilla review infrastructure, SQLite tracking, DuckDB analytics, and gold-label promotion.

Argilla exports are review transport only. They are not canonical truth until rows pass strict import validation and the reviewer action makes them eligible for gold-label output.

## Fields

| Field | Meaning |
| --- | --- |
| `schema_version` | Review schema version. Current value: `review_schema_v1`. |
| `review_id` | Stable ID for the review task. |
| `provenance_id` | Stable ID tying the signal to a deterministic source artifact or candidate row. |
| `case_id` | Transcript/call identifier. |
| `signal_type` | Deterministic predicted signal family or review taxonomy label. |
| `topic` | Business topic or cue family, when available. |
| `transcript_section` | Prepared remarks, Q&A, operator/admin, or unknown. |
| `speaker_role` | Management, analyst, operator, customer, or unknown. |
| `evidence_text` | Exact evidence span shown to the reviewer. |
| `evidence_start_hint` | Optional character, segment, or message-index hint. |
| `evidence_end_hint` | Optional end hint for the evidence span. |
| `predicted_direction` | Deterministic directional cue, when available. |
| `reviewer_action` | Human decision. Allowed values are listed below. |
| `reviewer_notes` | Optional reviewer rationale. Do not use for private notes. |
| `confidence` | Deterministic confidence from `0.0` to `1.0`. |
| `source_url` | Public source URL when available. |
| `transcript_path` | Local transcript artifact path or source reference. |
| `created_at` | UTC timestamp for task creation. |
| `reviewer_id` | Reviewer identifier supplied at review/import time. |
| `review_status` | Workflow state. See lifecycle states below. |
| `assigned_reviewer_id` | Optional reviewer assignment before review starts. |
| `reviewer_action_audit` | Deterministic audit payload recording imported action metadata. |
| `disagreement_status` | `none`, `reviewer_disagreement`, `adjudication_required`, or `resolved`. |
| `adjudication_notes` | Non-private adjudication notes when reviewer disagreement needs resolution. |
| `evidence_mismatch_class` | `none`, `exact_mismatch`, `partial_mismatch`, `transcript_missing`, or `section_mismatch`. |

## Allowed Review Actions

- `accept`: evidence, label, section, and direction are acceptable as shown.
- `reject`: the candidate should not become a gold label.
- `edit`: the candidate is directionally right, but evidence, section, direction, or wording needs correction.
- `relabel`: the evidence is useful, but the signal type must change.
- `uncertain`: the reviewer cannot decide from the visible evidence.

No other review action is valid.

## Lifecycle States

Allowed operational states are:

- `pending`
- `in_review`
- `accepted`
- `rejected`
- `edited`
- `relabeled`
- `uncertain`
- `adjudication_required`

Only validated rows with reviewer actions `accept`, `edit`, or `relabel` and matching states `accepted`, `edited`, or `relabeled` may become canonical gold labels.

Never silently promote:

- `pending`
- `in_review`
- `uncertain`
- `rejected`
- `adjudication_required`

Allowed transitions are intentionally narrow: candidates start as `pending`, move through `in_review` or directly to a reviewed terminal state, and only disputed terminal states may move to `adjudication_required`. Adjudicated rows may resolve to accepted, rejected, edited, relabeled, or uncertain.

## Provenance Enforcement

Exports write a deterministic manifest containing schema version, tool version, timestamps, row counts, review IDs, and provenance IDs. Imports must reference that manifest. If an imported row changes `review_id` or `provenance_id`, import fails closed.

If `transcript_path` exists, the evidence span is checked against the transcript text. Exact matches are recorded as `none`; partial overlap is `partial_mismatch`; missing transcript paths are `transcript_missing`; missing evidence is `exact_mismatch`; section conflict is `section_mismatch`.

## Evidence Standards

Evidence must be directly visible in the transcript and strong enough for another reviewer to understand the decision without guessing. A row should be rejected or marked uncertain when the evidence depends on outside context not preserved in the source artifact.

Evidence spans should be short enough to inspect, but long enough to preserve the speaker's claim, hedge, or commitment. Do not promote boilerplate, operator instructions, or generic safe-harbor language unless the signal specifically concerns those sections.

## Ambiguity Handling

Use `uncertain` when a row has plausible competing interpretations. Use `edit` when the deterministic signal is mostly correct but the span or direction needs a bounded correction. Use `relabel` when the evidence is valid but belongs to another canonical signal type.

Guidance ambiguity should remain explicit. If management language implies a directional change but does not state enough to compare against prior guidance, mark the row `uncertain` unless a separate source-backed field resolves the comparison.

## Disagreement Handling

Reviewer disagreement is a review lifecycle event, not a model failure by itself. Preserve the original deterministic prediction, reviewer action, reviewer ID, and notes. Do not overwrite evidence spans silently.

## Weak Evidence

Weak evidence should not become gold. Reject rows that rely on vague sentiment, broad summarization, or isolated keywords without a business claim. Mark as uncertain when the evidence may be useful but needs more surrounding context.
