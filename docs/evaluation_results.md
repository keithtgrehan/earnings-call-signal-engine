# Evaluation Results

Evaluation artifacts live in `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/data/processed/multimodal_engine`.

The current smoke evaluation is a reproducibility and wiring check, not a gold-label performance claim. Text model metrics are bounded to the current local human-reviewed seed labels. A validated model requires a real held-out benchmark with stable splits.

## Stage Summary

```json
{
  "ingest": "completed",
  "align": "completed",
  "text": "completed",
  "audio": "completed",
  "video": "completed",
  "fusion": "completed",
  "ensemble": "completed",
  "train": "completed",
  "evaluate": "completed",
  "active-learning": "completed"
}
```

## Claim Boundary

- Self-consistency rows prove the pipeline runs end to end.
- Text model metrics are bounded to the current local human-reviewed seed set.
- Multimodal uplift and cross-domain degradation remain explicit `requires labels` outputs until aligned multimodal gold labels exist.
- Weak labels, model predictions, and optional LLM triage are not gold labels.
