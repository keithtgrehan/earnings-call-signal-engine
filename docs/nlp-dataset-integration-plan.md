# NLP Dataset Integration Plan

Signal Engine should stay transcript-first and evidence-backed. Public datasets can help with sanity checks and baselines, but they must not replace local human-reviewed labels for the target domains.

## Local Storage Rules

- Raw external datasets stay in ignored local folders under `data/external/`.
- Large generated outputs, raw transcripts, PDFs, audio, video, caches, and model artifacts are not committed.
- Every external dataset needs a source note, license note, local path, and timestamped setup manifest.
- If a dataset requires manual download or license review, the repo should provide instructions only.

## Financial Datasets

| Dataset | Loader | Manifest | Raw local data | Status |
| --- | --- | --- | --- | --- |
| Financial PhraseBank | `scripts/import_financial_phrasebank.py` | `scripts/setup_financial_phrasebank.py` creates local manifest | Manual only | Ready for local licensed export |
| Loughran-McDonald | `scripts/import_loughran_mcdonald.py` | `scripts/setup_loughran_mcdonald.py` creates local manifest | Manual only | Ready for official CSV export |
| FiQA | Reference docs only | Research manifest references | Not present | Manual future loader |
| Financial Twitter sentiment | Setup script only | `scripts/setup_financial_twitter_sentiment.py` creates local manifest | Not present | Blocked until source/license/schema confirmed |
| SEC / 8-K | `scripts/fetch_sec_8k_index.py` support exists | Docs exist | Not committed | Metadata-first; raw filings remain local |

## Sales, Support, Renewals, And HR Datasets

- Sales: use user-owned call transcripts or CRM exports only after privacy review and redaction.
- Support: use user-owned ticket/call exports only after privacy review and redaction.
- Customer success / renewals: use account reviews, QBRs, and renewal calls only with explicit retention and privacy controls.
- HR / people conversations: use only synthetic fixtures or explicitly approved internal data; no sensitive inference claims.

## Privacy Constraints

- Apply deterministic redaction before sharing or committing review artifacts.
- Do not store secrets, customer identifiers, employee identifiers, or raw private conversations in git.
- HR data requires the highest caution: evidence-backed spans only, no diagnosis, no hidden-intent claims.

## Licensing Constraints

- Public availability is not the same as permission to redistribute.
- Financial PhraseBank and Loughran-McDonald require manual license review.
- Social-media datasets may have platform terms that restrict storage or redistribution.
- Commit loaders, manifests, and docs; keep raw data local.

## Ready Now

- Earnings-call transcript corpus pipeline.
- Deterministic weak labels.
- Human review packets.
- Draft selected-candidate conversion.
- Final human-approved conversion with overwrite guard.
- Final and draft evaluation separation.

## Manual Remaining Work

- Keith reviews draft selected candidates.
- Keith explicitly approves selected candidate IDs as human gold labels.
- External dataset source files are downloaded manually only after license review.
- New domain fixtures are expanded with human-reviewed labels before performance claims.
