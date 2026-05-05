# Signal Engine 2.0 Full Research Synthesis

## 1. What These Papers Collectively Teach

The list is not a single architecture prescription. It teaches a progression: simple description-length thinking, sequence memory, attention and pointers, residual/additive design, graph and relational structure, speech/vision foundations, and scaling discipline. The strongest shared lesson for Signal Engine 2.0 is that intelligence should be made observable through evidence, ablations, and staged evaluation.

## 2. What Is Immediately Useful For Signal Engine

- Evidence-first retrieval inspired by attention and pointer mechanisms.
- Transcript sectioning and callback tracking inspired by RNN/LSTM memory.
- Simplicity and weak-label governance from MDL and regularization papers.
- Residual sidecar design that preserves deterministic outputs.
- Reviewer-facing validation metrics before production ML claims.

## 3. What Is Useful Only After 100+ Labeled Transcripts

- Optional transformer or embedding reranker baselines.
- Learned sequence classifiers for uncertainty, friction, and guidance shifts.
- Active-learning loops trained on disagreement and false-positive patterns.
- Learning curves that compare feature complexity against held-out-call performance.

## 4. What Is Useful Only After Multimodal Assets Exist

- Deep Speech-style ASR quality gates and audio provenance tracking.
- Prosody and pause features joined to transcript spans.
- Video/visual sidecars evaluated as incremental lift over text.
- Speaker relation graphs that include audio/video timing only when legally safe media exists.

## 5. What Should Be Avoided

- Training large models before data volume and labels justify it.
- Treating attention weights as explanations without evidence-span validation.
- Committing raw PDFs or raw extracted source text without clear redistribution rights.
- Replacing deterministic Signal Engine behavior with a black-box model.
- Claiming market prediction or production-grade multimodal intelligence.

## 6. Feature Backlog

See `data/research/ilya_reading_list/signal_engine_feature_backlog.csv`. The backlog converts each paper into staged features with expected value, dependencies, and evaluation methods.

## 7. Evaluation Backlog

- Evidence-span precision/recall.
- Retrieval recall@k plus citation precision.
- Reviewer time-to-evidence.
- Weak-label false-positive reduction.
- Learning curves at 30, 100, and 500 transcripts.
- Text-only versus text+audio/video ablations after multimodal assets exist.

## 8. Dataset / Labeling Implications

The papers collectively argue for more careful labels, not more dramatic models. At 30 transcripts, stabilize taxonomy and evidence spans. At 100 transcripts, introduce held-out model baselines. At 500 transcripts, compare model families and relation/multimodal sidecars with credible ablations.

## 9. Architecture Implications

Signal Engine should remain a deterministic-first pipeline with optional sidecars: source registry, transcript memory, evidence pointer layer, retrieval memory, speaker relation graph, and evaluation dashboard. The raw transcript remains the source of truth.

## 10. Hiring / Portfolio Narrative

This asset shows research taste and product discipline: it connects landmark AI ideas to a concrete business NLP system while refusing to overclaim. It says: Keith can read frontier research, extract practical architecture choices, and keep evidence and evaluation ahead of hype.

## Parse Coverage

- Full text parsed locally: 24 papers.
- Non-full-text statuses are retained explicitly in `source_registry.json`.
