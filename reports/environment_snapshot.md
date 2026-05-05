# Environment Snapshot

Generated during the rebase recovery proof pass.

## Runtime

- Python: `3.11.3 (main, Jan 11 2026, 15:30:46) [Clang 15.0.0 (clang-1500.3.9.4)]`
- Platform: `macOS-26.2-arm64-arm-64bit`
- Repository path: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Branch: `codex/nlp-assets-tooling-registry`

## Key Package Versions

- `pytest==9.0.2`
- `ruff==0.15.1`
- `numpy==1.26.4`
- `pandas==2.3.3`
- `scikit-learn==1.8.0`
- `requests==2.32.5`
- `pypdf==5.9.0`
- `beautifulsoup4==4.14.3`
- `sentence-transformers==3.4.1`
- `faiss-cpu==1.13.2`
- `chromadb==0.5.23`

Not installed in this environment:

- `rapidfuzz`
- `rank-bm25`

## Notes

The deterministic evaluation loop and local ML smoke baseline do not require paid APIs. Optional embedding and dataset experiments remain gated by label count and explicit local asset availability.
