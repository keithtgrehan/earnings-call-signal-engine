# Retrieval Boundary

This note is intentionally narrow. It does not claim that a retrieval layer is implemented in the repo today.

## Built Now
- The canonical review path is transcript-first and deterministic-first.
- The current review units are deterministic artifact rows such as:
  - `guidance.csv`
  - `uncertainty_signals.csv`
  - `reassurance_signals.csv`
  - `analyst_skepticism.csv`
  - `metrics.json`
- For the canonical portfolio case, these live under [`outputs/PVH_2025_Q1_call09/`](../outputs/PVH_2025_Q1_call09/).

## Retrieval Boundary
- If this repo later grows a retrieval layer, the first retrieval unit should be a deterministic evidence object, not a generic raw chunk.
- That keeps retrieval grounded in auditable artifacts that already exist in the pipeline.
- A future retrieval/rerank layer should sit after deterministic extraction, not replace it.

## Evidence Object Shape
```json
{
  "case_id": "PVH_2025_Q1_call09",
  "artifact_type": "guidance_row",
  "source_file": "outputs/PVH_2025_Q1_call09/guidance.csv",
  "signal_family": "guidance",
  "text": "6.5 to 7%. Down, approximately 200 to 250 basis points compared to last year.",
  "segment_start": 2411.68,
  "segment_end": 2418.16,
  "metadata": {
    "topic": "other",
    "period": "Year",
    "guidance_strength": 0.72
  }
}
```

## Future Layer, Explicitly Not Built
- No vector index is implemented here today.
- No retrieval provider integration is implemented here today.
- No reranker is implemented here today.
- This note only defines the clean boundary between current deterministic artifacts and a future retrieval-facing interface.
