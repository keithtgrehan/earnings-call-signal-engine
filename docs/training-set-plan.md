# Training Set Plan

This plan tracks evaluation-set readiness without pretending that examples, weak labels, registries, or public dataset references are real validated training data.

## Current State

- No full real corpus is committed.
- No raw transcripts are added by this scaffold.
- No public datasets are downloaded.
- No model weights are committed.
- `data/gold_labels.example.jsonl` is a schema/evaluator example, not validated training data.
- Tiny fixtures are handcrafted smoke fixtures, not real earnings-call labels.
- Synthetic support, sales, and account-management examples are demos and smoke checks, not proof of product value.

## Planned Corpus Milestones

- `30_call_manual_gold_corpus`: first credible manually reviewed earnings-call benchmark target.
- `100_150_call_benchmark_corpus`: later benchmark after the 30-call workflow is stable.

Each real corpus case needs source confirmation, transcript rights review, local transcript handling, section review, speaker role review, manual labels, and evidence-span checks.

## Finance Candidates

Tracked finance candidates include Financial PhraseBank, FLAME, Open FinLLM, FINOS earnings-call transcript references, SEC 8-K/EDGAR metadata, Motley Fool, Seeking Alpha, Kaggle earnings-call references, and MAEC for later multimodal research.

These are candidate references only. They do not grant data rights, do not prove suitability, and are not downloaded by this repo.

## Sales / Support / Account Candidates

Tracked operational candidates include HubSpot, Salesforce, Gong, Chorus, Intercom, Zendesk, Freshdesk, Gainsight, churn labels, escalation labels, and objection labels.

These require user-owned exports and explicit privacy/licensing review. No CRM, call, ticket, or account-health export is committed.

## Emotion Candidates

Tracked emotion candidates include GoEmotions, DAIR.AI references, DailyDialog, MELD, EmotionLines, and EmpatheticDialogues.

These are benchmark references only. They are not product proof and do not validate emotion detection in business transcripts.

## Registry Use

`data/training_sets_registry.example.csv` and `data/training_sets_registry.example.json` track candidates, examples, and planned corpora. They are not a data license, not proof of download rights, and not evidence that a dataset is suitable for model training.

The deterministic transcript-first extraction path remains canonical until manually reviewed corpora and repeatable error analysis exist.
