# Signal Baseline Report

- scope: transcript-first wrapper for future multimodal evaluation
- status: `transcript_only_scaffold`
- multimodal_training_ready: `false`
- canonical path: deterministic transcript extraction

## Current Reality

- The repo does not yet include aligned text + audio + video fixtures with gold labels for a real multimodal lift study.
- This script therefore defaults to a transcript-only wrapper around the same weak-label baseline task used in the NLP tranche.

## Label Support

| label | support |
| --- | --- |
| risk_friction | 14 |
| opportunity_commitment | 9 |
| uncertainty_hedging | 1 |
| neutral | 0 |

## Status

No aligned multimodal fixtures are committed, and the local transcript-only weak-label corpus is not strong enough for an honest 4-class split.

## Limitations

- No aligned multimodal gold fixtures are committed in this Signal Engine 2.0 path.
- Local transcript weak labels remain too small or imbalanced for a stronger benchmark by default.
