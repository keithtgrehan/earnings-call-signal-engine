# Best-In-Class NLP Roadmap

## 1. What Best-In-Class Means For This Repo

Best-in-class here means rigorous, measurable, defensible transcript evaluation. It does not mean chasing the largest model or making stronger claims than the evidence supports.

## 2. What Is Measured Now

- transcript-first deterministic benchmark on `48` human-seeded labels
- majority baseline, deterministic rules, and exploratory TF-IDF classifier variants
- error analysis slices and reviewer-facing queues
- candidate gold holdout discipline
- retrieval scaffold for similar-example review

## 3. What Is Not Proven Yet

- statistical significance
- robust generalization across larger datasets
- inter-rater agreement
- multimodal lift from aligned audio/video
- transformer or LLM superiority over deterministic rules

## 4. Dataset Milestones

- `48` current: enough for first proof, error analysis, and workflow scaffolding
- `100` next: enough for a more meaningful benchmark refresh and stronger holdout discipline
- `300` stronger: enough to compare variants more responsibly and stress-test class balance

## 5. Label Quality Plan

- second reviewer on priority queue first
- Cohen’s kappa once reviewer labels exist
- promote a reviewed holdout into a true gold set only after agreement review

## 6. Model Ladder

- deterministic rules
- TF-IDF baseline
- embeddings and retrieval scaffold
- optional transformer benchmark
- LLM as evaluator only, not canonical scorer

## 7. Multimodal Plan

- transcript remains canonical
- audio prosody comes next if approved aligned clips exist
- video remains a sparse cue layer only

## 8. Research Source Priority

- Loughran-McDonald now
- Financial PhraseBank next
- Switchboard / MRDA next if access is justified
- FinBERT later as benchmark only
- openSMILE and OpenCV later as optional adapters
- MELD and CMU-MOSEI remain later research references, not default implementation targets

## 9. Next 30-Day Execution Plan

1. complete second review on the priority queue
2. promote a reviewed holdout into a real gold set
3. grow the labeled dataset toward `100`
4. rerun benchmark and error analysis
5. add `4` to `6` approved aligned audio clips for the pilot

## 10. Failure Criteria

- any claim of superiority without stronger data
- any benchmark that trains on locked holdout rows
- any canonical path that depends on heavy models
- any use of audio/video cues as hidden-state proof
