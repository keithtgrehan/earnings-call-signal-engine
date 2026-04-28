# Training Set Plan

This plan tracks evaluation-set readiness without pretending that examples, weak labels, or registries are real validated training data.

## Current State

- No full real corpus is committed.
- No raw transcripts are added by this scaffold.
- `data/gold_labels.example.jsonl` is a schema/evaluator example, not validated training data.
- Tiny fixtures are handcrafted smoke fixtures, not real earnings-call labels.
- Synthetic support, sales, and account-management examples are useful demos, not proof of product value.

## First Credible Milestone

The first credibility unlock remains a 30-call manually reviewed real earnings-call corpus. Each case needs source confirmation, local transcript handling, section review, speaker role review, manual labels, and evidence-span checks.

## Next Milestone

After the 30-call process is stable, expand to a 100-150 call benchmark. Do not benchmark production ML, embeddings, rerankers, or long-context review until deterministic labels and error analysis are reliable.

## Registry Use

`data/training_sets_registry.example.csv` and `data/training_sets_registry.example.json` track candidates, examples, and planned corpora. They are not a data license, not proof of download rights, and not evidence that a dataset is suitable for model training.
