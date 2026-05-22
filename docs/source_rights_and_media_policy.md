# Source Rights and Media Policy

Signal Engine treats transcript text as canonical and media as optional support. Publicly available does not mean reusable.

## Source Classes

- Official IR: metadata-only until site terms and robots status are checked; raw use requires explicit registry permission.
- SEC/EDGAR: public filing metadata and companyfacts are metadata/fair-access sources; raw exhibits still require source-specific review.
- YouTube metadata: URL/platform metadata can be registered; raw audio/video is blocked by default.
- Manual local: user-supplied file paths can be registered without copying file content into the repo.
- Licensed vendor: blocked unless an explicit license config permits raw ingest, storage, commit, training, and evaluation.
- Restricted/paywalled/login sources: blocked for raw ingest, commit, training, and evaluation.

## Agent 5 Acquisition Rules

Source discovery and acquisition must keep these source types separate:

- `official_ir`: preferred official source when terms allow use;
- `sec_edgar`: metadata/facts/filing-reference source, with fair-access behavior and conservative rate limits;
- `licensed_vendor`: blocked unless explicit license config permits raw ingest and downstream use;
- `manual_local`: operator-supplied file path registration, no raw copying by default;
- `youtube_metadata`: URL/platform metadata only by default;
- `restricted_paywalled_login`: blocked case tracking only.

Required source fields:

- transcript/audio/video availability;
- `source_terms_checked`;
- `robots_checked` or equivalent robots status;
- paywall/login status;
- `raw_body_allowed`;
- `commit_allowed`;
- `training_allowed`;
- `eval_allowed`;
- `blocked_reason`.

Blocked cases are first-class records. A blocked source is useful for coverage planning, but not for raw transcript/audio/video ingest.

## Required Registry Posture

Every source must represent rights tier, allowed storage, commit permission, training/eval permission, raw-body permission, source terms status, robots status, paywall/login status, provenance hash, and blocked reason.

Unknown rights fail closed. Raw transcript/audio/video bodies must not be committed. No workflow may bypass robots, paywalls, logins, platform terms, or vendor restrictions.
