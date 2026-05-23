# A/B And Multivariate Evaluation Design

Supported variants:

- `deterministic_only`
- `deterministic_plus_retrieval`
- `deterministic_plus_byok_reviewer`
- `deterministic_plus_audio_metadata`
- `deterministic_plus_event_study_context`

Default local checks run no provider calls and no market data fetches.

BM25 should be evaluated before dense retrieval. Evidence citation validity is required before reviewer usefulness claims.
