# Research To Feature Matrix

| Paper | Category | Candidate Feature | Evaluation Gate | Status |
|---|---|---|---|---|
| The First Law of Complexodynamics | `compression_mdl_complexity` | Compression ratio feature for prepared remarks vs Q&A | Compare compression/novelty scores against human evidence-span labels | `research_only` |
| The Unreasonable Effectiveness of Recurrent Neural Networks | `sequence_models` | Character/word baseline language model probes | Train tiny local baselines only after enough transcripts | `research_only` |
| Understanding LSTM Networks | `sequence_models` | Section memory features | Check whether later Q&A references earlier prepared remarks | `research_only` |
| Recurrent Neural Network Regularization | `sequence_models` | Regularized local baseline checklist | Track train/dev gap by transcript count | `research_only` |
| Keeping Neural Networks Simple by Minimizing the Description Length of the Weights | `compression_mdl_complexity` | Model complexity budget | Compare simple deterministic features to optional learned baselines | `research_only` |
| Pointer Networks | `attention_transformers` | Pointer-style evidence selector | Evidence-span precision/recall | `research_only` |
| ImageNet Classification with Deep Convolutional Neural Networks | `vision_multimodal` | Visual frame feature candidate registry | Only evaluate visual features when source coverage and labels exist | `research_only` |
| Order Matters: Sequence to Sequence for Sets | `sequence_models` | Permutation stress test for chunk rankers | Shuffle candidate evidence spans and measure stability | `research_only` |
| GPipe: Easy Scaling with Micro-Batch Pipeline Parallelism | `scaling_systems` | Compute readiness checklist | Record cost/performance only after local baselines saturate | `research_only` |
| Deep Residual Learning for Image Recognition | `vision_multimodal` | Additive evidence scoring layers | Ablate each sidecar as a residual contribution | `research_only` |
| Multi-Scale Context Aggregation by Dilated Convolutions | `vision_multimodal` | Local/medium/global transcript window features | Compare single-sentence vs neighboring-window evidence quality | `research_only` |
| Neural Message Passing for Quantum Chemistry | `graph_relational_learning` | Speaker-turn graph scaffold | Evaluate graph features against Q&A friction labels | `research_only` |
| Attention Is All You Need | `attention_transformers` | Attention-inspired chunk reranker | Compare lexical retrieval vs embedding/reranker candidates | `research_only` |
| Neural Machine Translation by Jointly Learning to Align and Translate | `attention_transformers` | Signal-to-evidence alignment report | Gold evidence alignment precision | `research_only` |
| Identity Mappings in Deep Residual Networks | `representation_learning` | Non-destructive scoring pipeline notes | Verify sidecars never remove source evidence | `research_only` |
| A Simple Neural Network Module for Relational Reasoning | `graph_relational_learning` | Speaker relation features | Evaluate whether answer-evasion labels improve with Q/A pair features | `research_only` |
| Variational Lossy Autoencoder | `representation_learning` | Lossy summary audit | Measure whether summaries preserve gold evidence spans | `research_only` |
| Relational Recurrent Neural Networks | `reasoning_memory` | Multi-thread call state tracker | Evaluate callback detection across sections | `research_only` |
| Quantifying the Rise and Fall of Complexity in Closed Systems: The Coffee Automaton | `compression_mdl_complexity` | Signal density curve | Compare signal density by call phase | `research_only` |
| Neural Turing Machines | `reasoning_memory` | Evidence memory store | Evaluate retrieval memory hit rate | `research_only` |
| Deep Speech 2: End-to-End Speech Recognition in English and Mandarin | `speech_audio` | ASR provenance manifest | Track ASR word error on any manually checked clips | `research_only` |
| Scaling Laws for Neural Language Models | `scaling_systems` | Transcript-count gates | Plot learning curves for local baselines by transcript count | `research_only` |
| A Tutorial Introduction to the Minimum Description Length Principle | `evaluation_theory` | Model selection notes | Track errors saved per added feature | `research_only` |
| Machine Super Intelligence | `evaluation_theory` | Capability-claim checklist | Audit product language for unsupported AI claims | `research_only` |
| Kolmogorov Complexity and Algorithmic Randomness | `compression_mdl_complexity` | Boilerplate/compressibility research note | Validate compression metrics against human labels | `research_only` |
| Stanford's CS231n Convolutional Neural Networks for Visual Recognition | `vision_multimodal` | Multimodal learning syllabus | Require visual feature coverage reports | `research_only` |
