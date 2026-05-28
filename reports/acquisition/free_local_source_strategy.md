# Free/Local Source Strategy

Signal Engine uses transcript-first, rights-gated ingestion for the NYSE 100 workspace.

- SEC EDGAR is metadata-first for CIK, 8-K, Exhibit 99.1, and event identity discovery.
- Company IR is metadata-first unless a row is explicitly promoted into the user-authorized permitted-download manifest.
- Manual-local transcripts and audio are registered by Desktop path and sha256 only.
- Local ASR and audio features are optional support layers; no cloud upload is enabled by default.
- Retrieval readiness is lexical/BM25 manifest-first; embeddings and vector databases are not written to git.
- Paid/vendor APIs remain disabled by default and require `license_config_ref` before any future raw access.

Guardrails:

- Raw transcripts/audio/video/ASR text stay outside git.
- `commit_allowed=false` for raw assets.
- `training_allowed=false` unless an explicit training-rights reference exists.
- YouTube media, paywall/login/DRM/session URLs, and unlicensed vendor raw content remain blocked.
