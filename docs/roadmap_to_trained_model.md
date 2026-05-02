# Roadmap To Trained Model

## Phase 1 - Benchmark Foundation

- Parse the current `31` calls and packet data into benchmark-ready segment candidates.
- Create a review queue from uncertainty, disagreement, rare labels, and high-value business segments.
- Convert reviewed examples into human gold labels only after explicit approval.
- Create train/dev/test splits with saved manifests and stable random seeds.
- Evaluate the current text baseline against the gold text benchmark.

Exit gate: held-out text benchmark exists with enough support for each business signal family.

## Phase 2 - Text Model Quality

- Train and track a TF-IDF baseline.
- Train and track a transformer baseline.
- Compare FinBERT, DeBERTa, RoBERTa, and DistilBERT-family candidates.
- Add ensemble comparisons against deterministic rules, weak labels, baseline classifiers, and transformer outputs.
- Add metric regression checks so future changes cannot silently degrade precision, recall, F1, calibration, or confusion-matrix behavior.

Exit gate: a text model beats deterministic and majority baselines on a real held-out benchmark without hiding false positives or false negatives.

## Phase 3 - Audio

- Collect local audio examples with known transcript alignment.
- Run Whisper/faster-whisper alignment and preserve timestamps.
- Extract OpenSMILE and librosa features such as pauses, speech rate, pitch, energy, jitter, shimmer, and intensity proxies.
- Evaluate audio-only and text+audio pipelines.
- Measure uplift against text-only and document cases where audio hurts or adds no value.

Exit gate: text+audio evaluation is measured on aligned examples with human gold labels.

## Phase 4 - Video

- Collect local video examples with reviewable segment windows.
- Run segment-triggered OpenCV, MediaPipe, and DeepFace feature extraction.
- Evaluate video-only and text+audio+video pipelines.
- Keep video outputs limitation-aware and never treat facial or engagement proxies as certain hidden-state truth.

Exit gate: text+audio+video evaluation includes ablation results and evidence windows.

## Phase 5 - Active Learning

- Sample model disagreement cases.
- Sample low-confidence cases.
- Sample rare labels.
- Sample high-value risk, escalation, uncertainty, and commitment segments.
- Keep human review minimal and targeted.
- Promote labels to gold only through explicit human approval.

Exit gate: review batches measurably improve benchmark coverage and reduce uncertainty in priority labels.

## Phase 6 - Remote Compute Readiness

- Finalize dataset manifests and checksums.
- Save train/dev/test splits.
- Write training configs for text, audio, video, fusion, and ensemble runs.
- Track every run in MLflow with params, metrics, artifacts, code version, and dataset manifest.
- Create reproducible scripts for local smoke, CPU training, and GPU training.
- Prepare a GPU job plan with expected runtime, storage, and rollback behavior.

Exit gate: remote jobs can be launched from stable configs and reproduced locally on a small subset.
