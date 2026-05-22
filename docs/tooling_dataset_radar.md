# Tooling and Dataset Radar

This radar tracks candidate resources without making them canonical dependencies.

| Resource | Status | Rights posture | Default use | Recommendation |
| --- | --- | --- | --- | --- |
| SEC EDGAR/companyfacts | scaffolded | public-domain/fair-access metadata | event metadata and public filing facts | Use metadata first; no aggressive polling. |
| Company IR pages | gated | official terms checked per source | transcript-first corpus when allowed | Require robots/site terms and provenance before raw storage. |
| FRED macro series | scaffolded | source-owner terms can vary by series | macro context | Check series-level terms before storing values. |
| Loughran-McDonald | supported | public academic resource, terms review before vendoring | deterministic lexicon support | Keep as deterministic support. |
| Financial PhraseBank | benchmark-only | verify local dataset terms | sanity-check comparator | Never merge rows into gold. |
| Argilla | optional support | local review data | human-review workflow | Use only for reviewer workflow, not label automation. |
| Label Studio | fallback | local review data | annotation fallback | Use if Argilla is too heavy. |
| Restricted transcript vendors | blocked | subscription/login/vendor terms | none by default | Do not copy, commit, train, or evaluate on raw bodies without explicit license. |
| Embeddings/retrieval | gated support | depends on underlying corpus rights | reviewer support | Retrieve evidence objects before fine-tuning. |
| Fine-tuning | gated | requires reviewed-label rights and sample size | later benchmark | Defer until retrieval and deterministic error analysis justify it. |

The machine-readable starter radar is `configs/dataset_radar.example.yml`.
