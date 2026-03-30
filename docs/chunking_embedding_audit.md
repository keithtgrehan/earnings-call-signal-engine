# Chunking + Embedding Audit

## Scope

This audit covers the current transcript-first deterministic pipeline and the new bounded place where supporting-only retrieval can fit without weakening canonical outputs.

## What Already Exists

### Transcript chunk creation

- Core chunking helpers already exist in `src/earnings_call_sentiment/chunking.py` and `src/earnings_call_sentiment/review_workflow.py`.
- Fixed demo cases such as Netflix and NVIDIA build transcript review units by:
  - parsing transcript blocks into a cleaned transcript
  - splitting long blocks with `chunk_text_for_review(...)`
  - assigning bounded synthetic timings per block chunk
  - writing `processed/chunks/chunks_scored.csv`, `processed/chunks/chunks_scored.jsonl`, and `processed/chunks/segment_metadata.json`
- For the Netflix reference case, this happens in `scripts/build_netflix_demo_case.py` via:
  - `build_synthetic_segments(...)`
  - `write_chunks_scored_artifacts(...)`

### Deterministic review artifacts already present

Netflix already has deterministic or transcript-backed artifacts for all of the bounded source types needed for an initial retrieval sidecar:

- Transcript chunks:
  - `data/demo_cases/netflix_q1_2022/processed/chunks/chunks_scored.jsonl`
  - `data/demo_cases/netflix_q1_2022/processed/chunks/segment_metadata.json`
- Transcript block structure:
  - `data/demo_cases/netflix_q1_2022/processed/transcript_text/transcript_sectioned.json`
- Q&A pairs:
  - `data/demo_cases/netflix_q1_2022/processed/qa_pairs/qa_pairs.json`
- Guidance spans:
  - `data/demo_cases/netflix_q1_2022/processed/signals/guidance.csv`
- Q&A shift context:
  - `data/demo_cases/netflix_q1_2022/processed/signals/qa_shift_summary.json`
  - `data/demo_cases/netflix_q1_2022/processed/signals/qa_shift_segments.csv`
- Shareholder-letter evidence:
  - `data/demo_cases/netflix_q1_2022/processed/transcript_text/shareholder_letter_text.txt`
  - `data/demo_cases/netflix_q1_2022/processed/signals/shareholder_letter_evidence.json`
- Curated transcript-first review moments:
  - `data/demo_cases/netflix_q1_2022/processed/joined_review/joined_review_moments.json`
  - `data/demo_cases/netflix_q1_2022/demo/evidence_rows/netflix_q1_2022_evidence_rows.json`
- Curated audio-support rows:
  - `data/demo_cases/netflix_q1_2022/processed/audio_behavior/audio_review_rows.json`

### Existing supporting-only precedent

The repo already has a clear pattern for optional sidecars that do not replace deterministic outputs:

- `src/earnings_call_sentiment/nlp_sidecar.py`
- `data/processed/multimodal/nlp/...`

That sidecar pattern is useful because it already states the right boundary:

- deterministic labels remain source of truth
- extra model outputs are inspectable support only

## What Does Not Exist Yet

- No embedding/vector retrieval module existed in `src`.
- No vector search CLI existed.
- No retrieval bundle existed under the Netflix demo case.
- No `mpnet`-style support existed in repo code.
- No sentence embedding dependency such as `sentence-transformers` existed as a first-class package dependency.
- No vector database or ANN index existed in the project.

## Dependency / Runtime Surface

Available already:

- `transformers`
- `torch`
- `numpy`
- `pandas`
- `scikit-learn` in `requirements.txt`

Not present as an existing repo feature:

- FAISS
- Annoy
- HNSW infra
- sentence-transformers package
- mpnet-specific helper code

Conclusion:

- a lightweight file-based bundle is the natural first implementation
- optional embeddings can be computed with the existing `transformers` + `torch` stack
- a vector DB would be unnecessary infra sprawl for this phase

## Most Natural Storage Format

For this repo, the most natural first bounded storage format is:

- JSONL for normalized retrieval rows
- JSON for bundle metadata / manifest
- optional NumPy `.npy` for embedding vectors
- local README in the bundle directory

Why this fits:

- reviewable in Git
- easy to diff
- aligns with existing case-pack artifact patterns
- no new service or database requirement

## Safe Fit For Embeddings

Embeddings can fit safely only as a derived sidecar over already-bounded artifacts:

- transcript chunks
- analyst question spans
- Q&A answer spans
- guidance spans
- shareholder-letter paragraphs
- optional curated multimodal rows only when clearly flagged as support

Embeddings should not:

- replace chunk creation
- replace deterministic span generation
- collapse provenance into free-form summaries
- become a scoring or “truth” layer

## Canonical vs Supporting-Only Boundary

Canonical remains:

- transcript-backed chunks
- deterministic span files
- deterministic guidance / QA / review artifacts
- explicit transcript excerpts and source locators

Supporting-only can now include:

- lexical retrieval over those bounded rows
- embedding similarity over the same bounded rows
- row-to-row similarity for navigation
- reviewer follow-up search that preserves provenance fields

## Missing Pieces Before This Work

- normalized retrieval row schema
- manifest describing boundary / model / files
- optional embedding export path
- reusable hybrid search helper
- CLI for bounded case retrieval search
- docs that explain the canonical/supporting split in retrieval terms
