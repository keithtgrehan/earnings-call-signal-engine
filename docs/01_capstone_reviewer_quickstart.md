# Capstone Reviewer Quickstart

Signal Engine 2.0 is a transcript-first, deterministic earnings-call signal extraction pilot. The default local path is safe: no provider keys, no raw source downloads, no model training, and no automatic gold-label promotion.

## Built Now

- `signal-engine doctor --json` checks the local environment and core proof paths.
- Agent 1 deterministic candidate extraction reads only registered manual-local transcript paths.
- Agent 4 review queues, contamination preflags, calibration batches, packets, and promotion gates are local-only.
- Agent 5 source discovery builds metadata-only NYSE target/source availability maps.
- Agent 2 evaluation gates report readiness and claim boundaries without fetching market data.

## Scaffolded Now

- 500-call NYSE metadata universe readiness map.
- Official IR, SEC, webcast, YouTube metadata, and slides availability queues.
- Retrieval readiness over evidence objects with no embeddings or vector database.

## Not Ready / Blocked

- Real model training is blocked until at least 100 valid adjudicated labels pass validation.
- Raw transcript/audio/video/slides ingest is blocked unless source rights are explicit.
- Vendor raw ingest is blocked without `license_config_ref`.
- YouTube raw media/transcript use is blocked without explicit authorization.

## Local Checks

```bash
make doctor
make real-pilot-readiness-check
make capstone-ci
```

These checks must remain network-free and must not write canonical gold labels.
