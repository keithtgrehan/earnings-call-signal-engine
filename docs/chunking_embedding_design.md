# Chunking + Embedding Design

## Design Goal

Chunking remains the canonical review unit.

Embeddings and vector search are supporting-only additions for:

- navigation
- similarity grouping
- follow-up inspection
- reviewer-facing search

They do not replace deterministic outputs, and they do not make predictive or statistical claims.

## Principles

1. Transcript-backed deterministic artifacts remain canonical.
2. Retrieval rows are derived only from bounded artifacts already in the case pack.
3. Every retrieval row carries explicit provenance.
4. Lexical retrieval must work even when embeddings are unavailable.
5. Semantic similarity must be framed as a navigation aid, not adjudication.

## Retrieval Row Schema

Each row in the bundle carries these core fields:

- `row_id`
- `case_id`
- `source_type`
- `source_artifact`
- `source_locator`
- `moment_id`
- `chunk_id`
- `span_id`
- `text`
- `start_time_s`
- `end_time_s`
- `deterministic_category`
- `plain_english_label`
- `top_8_showcase`
- `supporting_only`

Additional metadata is preserved in:

- `section`
- `speaker`
- `speaker_role`
- `review_priority`
- `artifact_paths`
- `metadata`

## Supported Artifact Types

### Netflix default export

- `transcript_chunk`
- `analyst_question_span`
- `qa_answer_span`
- `guidance_span`
- `shareholder_letter_paragraph`

### Optional curated rows

The implementation supports an opt-in curated multimodal row type:

- `curated_multimodal_moment`

This stays off by default so the shipped retrieval packs remain transcript-first and avoid mixing excerpted audio interpretations into the primary text bundle.

### NVIDIA extension

The optional NVIDIA pack uses the same retrieval pattern, but the management-document artifact is:

- `press_release_paragraph`

That is a local case-shape fallback, not a broader scope rewrite.

## Source Mapping

### Transcript chunks

Source artifacts:

- `processed/chunks/chunks_scored.jsonl`
- `processed/chunks/segment_metadata.json`

Preserved metadata:

- `chunk_id`
- `segment_id`
- `block_id`
- `speaker`
- `speaker_role`
- sentiment label / signed score

### Analyst question spans

Source artifacts:

- `processed/transcript_text/transcript_sectioned.json`
- `processed/qa_pairs/qa_pairs.json`
- `processed/chunks/segment_metadata.json`

Preserved metadata:

- `qa_pair_id`
- question block id
- span timing from segment metadata

### Q&A answer spans

Source artifacts:

- `processed/transcript_text/transcript_sectioned.json`
- `processed/qa_pairs/qa_pairs.json`
- `processed/chunks/segment_metadata.json`

Preserved metadata:

- `qa_pair_id`
- answer block ids
- answer speaker list
- aggregated transcript-backed span timing

### Guidance spans

Source artifacts:

- `processed/signals/guidance.csv`
- `processed/chunks/chunks_scored.jsonl`

Preserved metadata:

- `guidance_strength`
- `topic`
- `period`
- matched cues
- linked `chunk_id` when exact chunk alignment exists

### Shareholder-letter paragraphs

Source artifacts:

- `processed/transcript_text/shareholder_letter_text.txt`
- `processed/signals/shareholder_letter_evidence.json`

Preserved metadata:

- paragraph index
- matched deterministic evidence labels

## Bundle Layout

### Netflix

- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_rows.jsonl`
- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_manifest.json`
- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_embeddings.npy`
- `data/demo_cases/netflix_q1_2022/demo/retrieval/README.md`

### NVIDIA

- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/nvidia_retrieval_rows.jsonl`
- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/nvidia_retrieval_manifest.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/nvidia_retrieval_embeddings.npy`
- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/README.md`

## Embedding Implementation

Default embedding model used in this change:

- `sentence-transformers/all-MiniLM-L6-v2`

Why this model:

- lightweight enough for a bounded file-based sidecar
- works with the repo’s existing `transformers` + `torch` dependencies
- no new vector DB or serving dependency required

Embedding behavior:

- row embeddings are written only when model loading succeeds
- lexical retrieval still works without embeddings
- query-time semantic search prefers the local cached model once the bundle exists

## Retrieval Behavior

### Lexical

- token overlap over bounded rows
- label/category text included for navigation
- simple pressure-oriented ranking boost for queries explicitly asking about pressure-style moments

### Semantic

- cosine similarity over the row embedding matrix
- can be driven by:
  - free-text query
  - existing `row_id` as a seed row

### Hybrid

- combines lexical and semantic ranking when embeddings are present
- falls back to lexical only when embeddings are missing

## Non-Goals

- no vector DB
- no ANN service
- no replacement of deterministic review logic
- no silent claim that nearest-neighbor similarity “proves” a transcript interpretation
- no predictive or statistical significance layer

## Canonical Boundary

Canonical:

- transcript chunks
- deterministic guidance / QA / case-pack artifacts
- transcript-backed source locators

Supporting-only:

- retrieval bundle rows
- lexical ranking
- embedding similarity
- row-seeded similarity browsing

The retrieval layer is deliberately non-canonical and provenance-preserving.
