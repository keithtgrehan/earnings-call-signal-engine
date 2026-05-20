# Productization Execution Plan

## Safe Now

- Use deterministic transcript-first rules as canonical output.
- Track source-quality subsets and fixture-excluded metrics.
- Use TF-IDF/logistic regression only as a benchmark and disagreement finder.
- Build retrieval evidence objects, but keep retrieval gated.
- Produce demo artifacts with explicit caveats.

## Premature

- Production ML claims.
- Statistical or alpha claims.
- Silent dataset downloads.
- Embeddings overriding deterministic signals.
- Large architecture rewrites or production vector DB scaling.

## Current Metric Direction

- precision: `0.8399`
- recall: `0.8326`
- F1: `0.8276`

## Confusion Snapshot

`{'risk_friction->risk_friction': 12, 'risk_friction->opportunity_commitment': 1, 'opportunity_commitment->opportunity_commitment': 13, 'opportunity_commitment->neutral': 2, 'uncertainty_hedging->risk_friction': 2, 'uncertainty_hedging->uncertainty_hedging': 13, 'uncertainty_hedging->opportunity_commitment': 3, 'neutral->opportunity_commitment': 2, 'neutral->neutral': 9}`
