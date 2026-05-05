# Architecture Implications

The list supports a layered architecture that preserves source evidence and deterministic behavior.

## Principles

- Preserve the raw transcript and evidence spans as first-class objects.
- Add research and ML sidecars as optional, auditable layers.
- Keep retrieval citation-first: every generated or classified claim should point back to text.
- Treat audio/video as provenance and feature sidecars until validated lift exists.
- Prefer explicit evaluation gates over broad AI claims.

## Suggested Future Components

- Transcript section memory: track prepared remarks, Q&A, callbacks, and guidance references.
- Evidence pointer layer: rank candidate spans without hiding deterministic scores.
- Retrieval memory: keyword/BM25 now, embeddings/rerankers later.
- Speaker relation graph: model analyst-question and management-answer pairs.
- Scaling dashboard: plot label volume, model complexity, cost, and held-out performance.

## Non-Goals For This Branch

- No production model implementation.
- No vector database.
- No paid API dependency.
- No change to existing pipeline behavior.
