# Retrieval Provider Dry Run

## Run status
- status: `retrieval_provider_adapter_scaffold_only`
- evaluated retrieval quality: `false`
- embeddings generated: `false`
- vector DB generated: `false`
- network calls: `false`
- provider benchmark complete: `false`
- production RAG claim: `false`

## Provider
- provider slot: `local_stub`
- provider type: `local_stub`
- provider mode: `dry_run`
- local_stub is the only enabled provider in this scaffold.
- External embedding and reranking providers are represented as disabled slots only.

## Inputs
- config path: `configs/retrieval_providers.example.yml`
- objects path: `data/retrieval/retrieval_object_metadata.jsonl`
- metadata object count: `512`
- metadata object digest: `sha256:9b6171fdc59d77e08d8b2ba53328a43a1556f749c657d0462ce3f20a1d11e779`

## Counts by object type
- event_aligned_chunk_metadata: `44`
- evidence_object_metadata: `44`
- semantic_chunk_metadata: `424`

## Counts by case_id
- bac_2025_q4: `13`
- cat_2024_q4: `12`
- cat_2025_q1: `13`
- cat_2025_q2: `23`
- cat_2025_q3: `23`
- cat_2025_q4: `23`
- f_2025_q1: `23`
- f_2025_q2: `22`
- f_2025_q3: `20`
- f_2025_q4: `21`
- hd_2024_q1: `22`
- hd_2024_q2: `23`
- hd_2024_q3: `23`
- hd_2024_q4: `22`
- hd_2025_q4: `22`
- jpm_2024_q1: `10`
- jpm_2024_q2: `6`
- jpm_2024_q3: `5`
- jpm_2024_q4: `6`
- jpm_2025_q1: `6`
- jpm_2025_q2: `5`
- jpm_2025_q3: `4`
- jpm_2025_q4: `5`
- lyb_2025_q1: `22`
- lyb_2025_q2: `23`
- lyb_2025_q3: `23`
- lyb_2025_q4: `21`
- rddt_2025_q2: `21`
- rddt_2025_q3: `2`
- rddt_2025_q4: `25`
- uber_2025_q4: `23`

## Safety
- This report contains metadata-only run metadata.
- No raw transcript text, ASR/audio text, chunk body text, provider response payloads, embeddings, vectors, indexes, or vector DB files are produced.
- This is adapter foundation only and does not benchmark provider quality.
- Later bakeoffs must use reviewed retrieval eval queries, explicit non-committed provider config, safe output locations, and artifact scans before metrics are interpreted.
