# Label Taxonomy

This benchmark uses transcript-first, human-reviewed labels for deterministic earnings-call signals. Weak labels are candidate system outputs only; gold labels require human review.

## Category Mapping

| Internal label | Portfolio-facing category |
| --- | --- |
| `guidance_revision` | Guidance / performance signal |
| `analyst_pressure` | Analyst pressure / friction signal |
| `uncertainty` | Uncertainty / hedge signal |
| `commitment` | Management commitment / opportunity signal |
| `neutral` | Neutral / no-signal evidence |

## Label Definitions

### `guidance_revision`

Use for revenue growth or decline, margin movement, outlook changes, above/below expectations, segment performance, guidance ranges, and forecast updates.

Include examples:

- Management updates revenue, EPS, margin, demand, or segment expectations.
- Management describes performance above or below prior expectations.

Exclude examples:

- Generic product descriptions.
- Legal disclaimers.
- Analyst questions without performance content.

### `analyst_pressure`

Use for analyst questions that probe ROI, capacity, competition, demand sustainability, margin pressure, macro risk, growth durability, CapEx, regulation, or execution risk.

Exclude generic clarifications, operator statements, and polite factual questions without friction.

### `uncertainty`

Use for meaningful cautious or risk language such as could, may, might, subject to, depends on, not possible to predict, risk, uncertainty, materially differ, headwinds, and volatility.

Avoid boilerplate uncertainty unless it is intentionally retained as disclosure-risk evidence. Suppress operator noise such as “You may disconnect your lines at this time.”

### `commitment`

Use for management action or intent, including “we will continue,” “we are investing,” “we are committed,” “we expect to,” “we plan to,” “we are focused on,” “we are expanding,” and “we see opportunity.”

Do not use for generic optimism, marketing fluff, or statements without action or direction.

### `neutral`

Use for factual, non-signal evidence. Neutral labels are important because they test false-positive behavior.

Good neutral examples include plain factual descriptions, accounting mechanics, schedule facts, and context that should not trigger a signal.

## Common False Positives

- Legal safe-harbor language counted as uncertainty.
- Operator instructions counted as uncertainty.
- Repeated vendor transcript headers counted as evidence.
- Generic management optimism counted as commitment.
- Product descriptions counted as guidance revision.

## Reviewer Rules

- Use exact transcript quotes only.
- Prefer full-sentence evidence.
- Avoid low-confidence examples in gold labels.
- Use `neutral` deliberately for likely false positives.
- Add short notes explaining why the label is human-confirmed.
- Do not convert weak labels or candidate snippets into gold labels without human review.
