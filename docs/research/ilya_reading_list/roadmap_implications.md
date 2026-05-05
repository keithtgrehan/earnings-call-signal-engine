# Roadmap Implications

The research points toward staged capability growth rather than a sudden black-box model replacement.

## Near Term: Deterministic And Review-First

- Keep deterministic transcript features as the default behavior.
- Add research metadata lookup and evidence-first feature planning.
- Use attention/pointer ideas to improve evidence-span review before model training.
- Use MDL/compression thinking to prefer simple features until measured lift exists.

## Mid Term: Optional Local ML Baselines

- Add small, optional baselines only after the 30-call benchmark has stable labels.
- Track overfitting using regularization, held-out calls, and train/dev gaps.
- Evaluate retrieval/reranking candidates against citation quality and reviewer agreement.

## Later: Multimodal And Scaled Systems

- Treat ASR/prosody as source-quality and evidence-alignment problems before model claims.
- Explore speaker-turn graphs and relation features after Q&A labels mature.
- Consider GPU-heavy or pipeline-parallel experiments only after 100-500 transcript gates.

## Research-Informed Gates

- 30 transcripts: deterministic labels, weak-label audit, retrieval scaffolds.
- 100 transcripts: local classifier/reranker smoke tests with strict holdouts.
- 500 transcripts: learning curves, model-family comparisons, optional GPU planning.
