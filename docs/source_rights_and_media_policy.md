# Source Rights and Media Policy

Signal Engine treats transcript text as canonical and media as optional support. Publicly available does not mean reusable.

## Source Classes

- Official IR: metadata-only until site terms and robots status are checked; raw use requires explicit registry permission.
- SEC/EDGAR: public filing metadata and companyfacts are metadata/fair-access sources; raw exhibits still require source-specific review.
- YouTube metadata: URL/platform metadata can be registered; raw audio/video is blocked by default.
- Manual local: user-supplied file paths can be registered without copying file content into the repo.
- Licensed vendor: blocked unless an explicit license config permits raw ingest, storage, commit, training, and evaluation.
- Restricted/paywalled/login sources: blocked for raw ingest, commit, training, and evaluation.

## Required Registry Posture

Every source must represent rights tier, allowed storage, commit permission, training/eval permission, raw-body permission, source terms status, robots status, paywall/login status, provenance hash, and blocked reason.

Unknown rights fail closed. Raw transcript/audio/video bodies must not be committed.
