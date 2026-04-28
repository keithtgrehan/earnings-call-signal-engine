# Local ML Baseline Plan

The local sklearn baseline is optional scaffolding only. It is not production ML and is not validated by smoke tests.

## Allowed Now

- Train from local JSONL rows supplied by the user.
- Use sklearn only if it is already installed.
- Write a JSON smoke report.
- Write a model artifact only if `--model-out` is explicitly provided.

## Not Allowed Now

- No external downloads.
- No paid APIs.
- No committed model weights.
- No claims of statistical significance.
- No claims that handcrafted fixtures or weak labels are real training data.

## Future Validation Requirement

Before any ML claim, the project needs held-out manually labelled data, repeatable metrics, documented false-positive analysis, and comparison against deterministic baselines.
