# Candidate Review Priority 30

This packet selects the highest-value mined candidate rows for a fast human review pass.

Selection priorities:

- neutral coverage
- clear risk_friction turns
- the small number of clean uncertainty_hedging examples
- short readable snippets
- strong evidence terms
- no obvious PII or placeholder-heavy rows

## Packet Mix

- `risk_friction`: `16`
- `opportunity_commitment`: `10`
- `uncertainty_hedging`: `2`
- `neutral`: `2`

## Notes

- This is a review queue, not an auto-promotion list.
- Candidate rows still require manual reviewer labels and explicit acceptance.
- Loughran-McDonald terms, when available, are evidence aids only.
