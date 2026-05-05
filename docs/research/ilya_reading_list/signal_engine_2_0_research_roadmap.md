# Signal Engine 2.0 Research Roadmap

This roadmap applies the reading-list findings directly to Signal Engine 2.0 while keeping current production claims unchanged.

## A. What Applies Now

- Deterministic transcript features: MDL, RNN regularization, and scaling-law lessons all favor simple baselines while data is small.
- Sequence-aware section modeling: RNN/LSTM and set-order papers justify prepared-remarks vs Q&A chronology, callback detection, and chunk-order stress tests.
- Attention-inspired retrieval: Bahdanau attention, Pointer Networks, and Transformers motivate citation-first retrieval and evidence-span ranking.
- Weak-label refinement: MDL and regularization ideas support rule audits, false-positive controls, and reviewer-centered label promotion.
- Evaluation design: Scaling laws and Machine Super Intelligence both argue for narrow claims, explicit metrics, and stage gates.

## B. What Applies Later

- Transformer baselines: only after enough labeled transcripts and held-out calls exist.
- Embedding/reranker experiments: add as optional sidecars, evaluated by citation quality and reviewer usefulness.
- Audio ASR/prosody from Deep Speech-style thinking: require legally safe audio, ASR provenance, and WER/proxy gates.
- Multimodal feature fusion: treat vision/audio as residual sidecars over transcript evidence, not replacements.
- Relational reasoning across speaker turns: model analyst-management Q&A pairs and topic-thread graphs after labels mature.
- Scaling laws for dataset growth: plot learning curves before increasing model complexity or compute.

## C. What Not To Do Yet

- Do not train large models.
- Do not overclaim AI reasoning.
- Do not add GPU-heavy systems.
- Do not replace the deterministic engine with a black-box model.
- Do not claim paper implementations when this branch adds research metadata and scaffolding only.

## D. 30/100/500 Transcript Roadmap

### 30 Transcripts

- Label strategy: stabilize taxonomy, evidence spans, and weak-label false-positive notes.
- Data threshold: enough for deterministic error analysis, not robust neural claims.
- Model candidates: deterministic rules, local keyword retrieval, optional tiny baseline smoke checks only.
- Evaluation gates: span-level precision/recall, reviewer agreement, section coverage.

### 100 Transcripts

- Label strategy: holdout split, second-review queue, active-learning candidate mining.
- Data threshold: enough for early local classifiers/rerankers if labels are consistent.
- Model candidates: regularized linear/sklearn models, small local embedding/reranker experiments if optional deps are available.
- Evaluation gates: held-out call performance, calibration, citation precision, ablation over deterministic baseline.

### 500 Transcripts

- Label strategy: stratified labels by sector, call phase, signal type, and speaker role.
- Data threshold: enough to compare model families and learning curves with less fragile estimates.
- Model candidates: transformer baselines, rerankers, relation graph features, audio/prosody sidecars where media is legally safe.
- Evaluation gates: lift over deterministic baseline, cost/latency report, error taxonomy, reviewer usefulness, and no unsupported market-prediction claims.
