# Human Review Workflow

Signal Engine treats deterministic transcript chunks and weak labels as review inputs, not truth. Human-reviewed labels are the only source that may become gold labels.

## Local Flow

1. Chunk transcripts deterministically:
   ```bash
   make review-load-transcripts
   ```
2. Convert deterministic weak labels into reviewer suggestions:
   ```bash
   make review-upload-suggestions
   ```
3. Build a prioritized queue:
   ```bash
   make review-build-queue
   ```
4. Review records in Argilla.
5. Export explicit reviewed records:
   ```bash
   REVIEWED_JSONL=/path/to/reviewed.jsonl make review-export-gold
   ```
6. Evaluate weak-label suggestions against reviewed truth:
   ```bash
   make review-eval
   ```

## Review States

- `pending`: chunk exists but has not been reviewed.
- `suggested`: deterministic weak labels are attached as suggestions.
- `reviewed`: a reviewer made an explicit decision.
- `approved`: a reviewed record is approved for gold export.
- `rejected`: reviewer rejected all suggested labels.
- `exported`: approved/reviewed labels were written to an export artifact.

Only `reviewed` and `approved` records can be exported. Suggestions are never promoted automatically.

## Provenance

Every record preserves:

- `case_id`
- `chunk_id`
- source file and source artifact
- section and speaker where available
- chunk offsets where available
- deterministic text hash
- provenance hash

Chunk IDs remain stable when transcript text and chunk parameters are unchanged. Changing chunk size, overlap, source path, offsets, or text changes the ID.

## Evaluation Caveat

Review evaluation compares weak-label suggestions to reviewed truth. If reviewed label volume is too small, metrics are skipped. Early metrics are useful for debugging the workflow, not for statistical benchmark claims.
