# NLP Model And Retrieval Roadmap

This roadmap separates implemented deterministic work from future model and retrieval experiments. It should not be read as a claim that production ML, retrieval, or market correlation is already validated.

## Implemented Now

- Deterministic parsers.
- Schemas.
- Text features.
- Role/turn features.
- Risk rules.
- Signal categories.
- Demo outputs.
- Synthetic support/sales/account examples.
- Existing text-emotion/label tooling if present.
- Dataset ingestion/proof tooling if present.
- Privacy/redaction scaffolding if present.

## Not Implemented Yet

- Production transformer model.
- Validated embedding retrieval stack.
- Reranker benchmark.
- 100-150 call gold dataset.
- Statistical uplift.
- Long-context benchmark matrix.
- Credible market-reaction correlation.

## Future Benchmark Candidates Only

- Embeddings: OpenAI, Voyage, Cohere, Jina.
- Rerankers: Cohere, Jina.
- Long-context review: OpenAI, Anthropic, Google.

## Recommended Sequence

1. Finish deterministic benchmark scaffolding.
2. Build and review the first 30-call manually labelled corpus.
3. Run error analysis and reduce false positives.
4. Expand to 100-150 calls only after label quality is stable.
5. Benchmark embeddings, retrieval, reranking, and long-context review as optional sidecars against deterministic outputs.
