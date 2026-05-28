# Operational Ingestion Summary

- Desktop workspace: `/Users/keith/Desktop/earnings calls 100 samples`
- Companies processed: 100
- Calls processed: 500
- Permitted download rows: 1000
- Transcript downloads attempted/succeeded: 500/0
- Audio downloads attempted/succeeded: 500/0
- Registered transcripts: 0
- Registered audio: 0
- Normalized transcripts: 0
- Transcript chunks: 0
- Evidence objects: 0
- Retrieval objects: 0
- Audio RAG records: 0
- BM25-ready objects: 0
- Agent 1 readiness: blocked_no_registered_transcripts
- Training readiness: blocked_training_rights_not_enabled
- Raw files committed: false
- Model training run: false
- Embeddings/vector DB committed: false

## Blockers

- No registered transcripts; normalization/chunking remain readiness-only.
- No registered audio; audio RAG remains readiness-only.

## Exact Next Manual Actions

- Review blocked download reasons for direct transcript/audio URLs.
- Place explicitly approved transcript/audio files in the Desktop workspace when manual-local is needed.
- Re-run registration, normalization, chunking, retrieval export, and audio RAG readiness after files are present.
