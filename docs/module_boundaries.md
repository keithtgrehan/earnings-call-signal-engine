# Module Boundaries

## Deterministic Core

Agent 1 sectioning, speaker roles, Q&A pairing, guidance comparison, candidate labels, evidence span refs, hashes, and provenance are canonical candidate generation logic.

## Reviewer Layers

Agent 4 review queues, contamination flags, reviewer packets, calibration batches, adjudication templates, and promotion manifests are reviewer workflow layers only. They do not mutate `data/gold/gold_labels.jsonl`.

## Acquisition Layers

Agent 5 performs rights-gated source discovery and permitted acquisition planning. Default outputs are metadata-only. Unknown rights fail closed.

## Evaluation Layers

Agent 2 reports readiness gates and benchmark scaffolds. Event-study context is exploratory and disabled unless required market/sector/price inputs are later approved.

## Retrieval Layers

Retrieval starts from evidence objects, then event-aligned chunks, then semantic chunks. No embeddings or vector DB artifacts are created by default.
