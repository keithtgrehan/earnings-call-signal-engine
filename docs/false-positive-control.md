# False-Positive Control

Signal Engine 2.0 should prefer fewer, more defensible signals over broad over-triggering. False-positive control is a core evaluation goal.

## Rules

- Generic positive or negative language is not enough.
- Uncertainty language is not automatically risk.
- Tone shift is not automatically guidance revision.
- Speaker role matters: management statements and analyst questions carry different meaning.
- Evidence span must justify the signal without relying on hidden context.

## Common Failure Modes

- Treating "strong demand" as a raised outlook without a guidance anchor.
- Treating "macro uncertainty" as risk friction without a material topic.
- Treating a prepared-remarks caution as analyst pressure.
- Treating analyst curiosity as pushback.
- Treating one isolated keyword as a full signal.

## Control Strategy

Use stable-control calls to measure over-triggering. Every rule should be reviewed against at least one stable case and one messy ambiguous case before promotion. Rules that fire often without clear evidence should be downgraded, topic-gated, or removed.
