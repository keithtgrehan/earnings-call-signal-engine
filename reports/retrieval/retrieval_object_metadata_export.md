# Retrieval Object Metadata Export

## Run status
- retrieval_object_status: `retrieval_object_scaffold_only`
- Retrieval object scaffold only.
- No embeddings are created or committed.
- No vector DB is created or committed.
- No evaluated retrieval quality or production RAG claims are made.

## Source and output
- Source manifest: `data/retrieval/retrieval_objects_manifest.csv`
- Output JSONL: `data/retrieval/retrieval_object_metadata.jsonl`
- Object count: `512`

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
- Output records contain metadata, hashes, span coordinates, and provenance references only.
- Raw transcript text, ASR/audio text, chunk body text, embeddings, vector payloads, vector DB files, provider artifacts, labels, adjudication rows, training data, and promotion rows are not produced by this export.
