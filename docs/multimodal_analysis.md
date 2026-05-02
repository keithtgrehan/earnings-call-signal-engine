# Multimodal Analysis

Principle: `TEXT = anchor; AUDIO + VIDEO = augmentation layers`.

## Fusion

```json
{
  "stage": "fusion",
  "status": "completed",
  "dry_run": false,
  "rows": 38,
  "notes": [
    "Fusion keeps text as anchor and treats audio/video as bounded adjustments."
  ]
}
```

## Ensemble

```json
{
  "stage": "ensemble",
  "status": "completed",
  "dry_run": false,
  "rows": 38,
  "review_recommended": 3
}
```

Audio and video outputs preserve `available`, `limitations`, and adapter metadata per segment. Side cues never override text evidence and disagreement remains visible in the ensemble output.

Current limitation: the fixture run has no local audio/video-backed training data. Multimodal uplift remains unproven until aligned media and human gold labels exist.
