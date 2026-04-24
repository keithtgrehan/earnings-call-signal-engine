# NLP Research Manifest

This manifest is a transcript-first research map for optional benchmarking and later model experiments.

- generated_at: `2026-04-24T17:29:14+00:00`
- entry_count: `22`
- canonical path: deterministic transcript extraction remains the source of truth

## Limitations

- Manifest is a curated starting point, not an exhaustive literature review.
- Entries are metadata only; datasets and model artifacts were not vendored by default.
- Access restrictions and licensing should be rechecked before any download or training use.

## Entries

### Dialogue Acts (`dialogue_acts`)

#### Switchboard Dialog Act Corpus
- type: `dataset`
- modality: `transcript`
- source: https://catalog.ldc.upenn.edu/LDC97S62
- relevance: Classic dialogue-act resource for Q&A turn structure, directness, and conversational move design.
- recommended use: Taxonomy and methodology reference; document metadata only unless licensed access is available.
- access/license: license_required: LDC access required.
- downloaded locally: `false`
- limitations: License-gated and not finance-specific.

#### ICSI Meeting Recorder Dialog Act Corpus (MRDA)
- type: `dataset`
- modality: `transcript`
- source: https://catalog.ldc.upenn.edu/LDC2004T12
- relevance: Useful reference for meeting-style dialogue acts, interruptions, and conversational structure.
- recommended use: Methodology reference for dialogue-act framing and annotation guidelines.
- access/license: license_required: LDC access required.
- downloaded locally: `false`
- limitations: Meeting domain differs materially from support, sales, and earnings calls.

### Earnings Calls (`earnings_calls`)

#### Modeling financial analysts' decision making via the pragmatics and semantics of earnings calls
- type: `paper`
- modality: `transcript`
- source: https://arxiv.org/abs/1906.02868
- relevance: Directly relevant to analyst pressure, Q&A pragmatics, and post-call interpretation features.
- recommended use: Research reference for transcript features around analyst-management friction and Q&A pressure.
- access/license: public: Public paper.
- downloaded locally: `false`
- limitations: Research correlations are not a license to claim predictive lift in this portfolio project.

#### Forecasting Earnings Surprises from Conference Call Transcripts
- type: `paper`
- modality: `transcript`
- source: https://aclanthology.org/2023.findings-acl.520/
- relevance: Strong earnings-call NLP reference tying transcript content to future surprise prediction tasks.
- recommended use: Research reference only for benchmark framing and task design, not for unsupported performance claims.
- access/license: public: Public paper; datasets may have separate access terms.
- downloaded locally: `false`
- limitations: Prediction framing is narrower and higher-risk than the repo's deterministic review focus.

#### Predicting Corporate Risk by Jointly Modeling Company Networks and Dialogues in Earnings Conference Calls
- type: `paper`
- modality: `transcript`
- source: https://arxiv.org/abs/2206.06174
- relevance: Relevant to dialogue-aware modeling and the limits of transcript-only risk inference.
- recommended use: Reference for future optional benchmark design around dialogue structure and risk cues.
- access/license: public: Public paper.
- downloaded locally: `false`
- limitations: Modeling setup is more ambitious than the current deterministic-first architecture.

#### SubjECTive-QA: Measuring Subjectivity in Earnings Call Transcripts' QA Through Six-Dimensional Feature Analysis
- type: `paper`
- modality: `transcript`
- source: https://arxiv.org/abs/2410.20651
- relevance: Highly aligned with bounded review cues for subjectivity, uncertainty, and question-answer quality.
- recommended use: Reference for future bounded QA-review taxonomies without turning subjectivity into canonical truth.
- access/license: public: Public paper.
- downloaded locally: `false`
- limitations: Published methodology still needs careful translation into reviewer-centric signals.

#### jlh-ibm/earnings_call dataset
- type: `dataset`
- modality: `transcript`
- source: https://huggingface.co/datasets/jlh-ibm/earnings_call
- relevance: Useful reference source for transcript structure and later optional finance-language benchmarking.
- recommended use: Metadata/reference only unless licensing is explicitly acceptable for local experiments.
- access/license: public: Check dataset card and underlying transcript rights before local use.
- downloaded locally: `false`
- limitations: Transcript rights and reuse terms may limit direct training use.

#### Aiera/aiera-transcript-sentiment dataset
- type: `dataset`
- modality: `transcript`
- source: https://huggingface.co/datasets/Aiera/aiera-transcript-sentiment
- relevance: Potential finance transcript sentiment benchmark candidate closer to earnings-call language than generic emotion corpora.
- recommended use: Optional benchmark reference only; do not vendor without checking terms.
- access/license: public: Review dataset card before use.
- downloaded locally: `false`
- limitations: Sentiment labels alone still under-specify guidance change, pressure, and evidence quality.

### Emotion Uncertainty (`emotion_uncertainty`)

#### GoEmotions
- type: `dataset`
- modality: `transcript`
- source: https://arxiv.org/abs/2005.00547
- relevance: Useful for optional fine-grained emotion benchmarking, especially as a contrast to business-domain signals.
- recommended use: Benchmark reference for optional text-emotion experiments only.
- access/license: public: Paper is public; dataset terms should be reviewed before local download.
- downloaded locally: `false`
- limitations: Reddit emotion labels are not the same thing as business-review signals or internal state.

#### EmpatheticDialogues
- type: `dataset`
- modality: `transcript`
- source: https://arxiv.org/abs/1811.00207
- relevance: Relevant as a contrastive dialogue corpus for empathy-like language, but not a direct fit for deterministic business review.
- recommended use: Reference only for future dialogue-style experiments, not as a direct product dataset.
- access/license: public: Dataset reuse depends on release terms.
- downloaded locally: `false`
- limitations: Empathy generation is far from earnings-call or support-ops review workflows.

### Financial Nlp (`financial_nlp`)

#### FinBERT: Financial Sentiment Analysis with Pre-trained Language Models
- type: `paper`
- modality: `transcript`
- source: https://arxiv.org/abs/1908.10063
- relevance: Strong finance-domain baseline reference for sentence-level sentiment benchmarking on financial text.
- recommended use: Reference model family for optional benchmark comparisons against deterministic transcript signals.
- access/license: public: Paper is public; model and downstream datasets have separate licenses.
- downloaded locally: `false`
- limitations: Sentiment labels do not map directly to guidance change, friction, or evidence quality.

#### ProsusAI/finbert model card
- type: `library`
- modality: `transcript`
- source: https://huggingface.co/ProsusAI/finbert
- relevance: Concrete local-model candidate for optional finance-specific benchmarking when cache is already available.
- recommended use: Optional offline benchmark adapter only; not canonical scoring.
- access/license: public: Use subject to model card and underlying dataset terms.
- downloaded locally: `false`
- limitations: Model-card availability does not guarantee local model cache or fit for earnings-call Q&A nuance.

#### Financial PhraseBank
- type: `dataset`
- modality: `transcript`
- source: https://huggingface.co/datasets/takala/financial_phrasebank
- relevance: Widely used sentence-level finance sentiment dataset that grounds benchmark comparisons for finance text.
- recommended use: Benchmark-only sentiment reference; useful for checking whether optional models behave sensibly on finance language.
- access/license: public: Dataset card should be reviewed before redistribution or bulk download.
- downloaded locally: `false`
- limitations: Short isolated sentences are a weak proxy for multi-speaker transcript review.

#### Loughran-McDonald Master Dictionary
- type: `library`
- modality: `transcript`
- source: https://sraf.nd.edu/loughranmcdonald-master-dictionary/
- relevance: Finance-specific lexicon reference for uncertainty and tone features without requiring black-box models.
- recommended use: Lexicon reference for deterministic or weak-label experiments on earnings-call language.
- access/license: public: Review site terms before vendoring any dictionary files.
- downloaded locally: `false`
- limitations: Dictionary counts need careful context handling and can overfire on long transcripts.

#### FiQA benchmark
- type: `benchmark`
- modality: `transcript`
- source: https://sites.google.com/view/fiqa/
- relevance: Finance QA and sentiment benchmark reference for optional retrieval and finance-language experiments.
- recommended use: Reference only for optional finance retrieval and question-answer benchmarking.
- access/license: public: Benchmark access and downstream dataset terms should be reviewed case by case.
- downloaded locally: `false`
- limitations: FiQA is not an earnings-call review dataset and does not validate conversation-level evidence quality.

#### FinNLI: Novel Dataset for Multi-Genre Financial Natural Language Inference Benchmarking
- type: `dataset`
- modality: `transcript`
- source: https://arxiv.org/abs/2504.16188
- relevance: Useful for reasoning-style benchmark planning around contradiction, entailment, and guidance language review.
- recommended use: Reference for optional contradiction and disclosure-consistency experiments.
- access/license: public: Check dataset release terms before local use.
- downloaded locally: `false`
- limitations: NLI labels do not directly validate reviewer usefulness in business-conversation workflows.

### Libraries (`libraries`)

#### spaCy
- type: `library`
- modality: `transcript`
- source: https://spacy.io/
- relevance: Useful optional library for tokenization, pattern matching, and lightweight rule-based NLP workflows.
- recommended use: Optional support library for deterministic extraction and offline preprocessing.
- access/license: public: See spaCy license and model-specific terms.
- downloaded locally: `false`
- limitations: Library support alone does not create validated business-review signals.

#### scikit-learn
- type: `library`
- modality: `transcript`
- source: https://scikit-learn.org/stable/
- relevance: Lightweight baseline-training stack for TF-IDF and classical classifiers without heavyweight models.
- recommended use: Use for weak-label baselines and benchmark scaffolding only.
- access/license: public: BSD-style open source license.
- downloaded locally: `false`
- limitations: Classical text baselines depend heavily on label quality and task framing.

### Support Sales (`support_sales`)

#### BANKING77
- type: `dataset`
- modality: `transcript`
- source: https://huggingface.co/datasets/PolyAI/banking77
- relevance: Good intent-detection reference for finance-adjacent customer requests and support language.
- recommended use: Benchmark reference for narrow-domain intent classification, especially support-style queries.
- access/license: public: Review dataset card before local use.
- downloaded locally: `false`
- limitations: Short user requests do not capture multi-turn review dynamics.

#### CLINC150
- type: `dataset`
- modality: `transcript`
- source: https://archive.ics.uci.edu/ml/datasets/CLINC150
- relevance: Intent classification baseline reference for weak-label or synthetic intent experiments.
- recommended use: Reference for intent taxonomy design and robustness checks.
- access/license: public: Use subject to UCI and original dataset terms.
- downloaded locally: `false`
- limitations: Assistant-intent framing does not directly capture escalation, evidence, or reviewer usefulness.

#### Schema-Guided Dialogue dataset
- type: `dataset`
- modality: `transcript`
- source: https://github.com/google-research-datasets/dstc8-schema-guided-dialogue
- relevance: Useful for slot/intent-oriented customer-service dialogue structure and domain-transfer thinking.
- recommended use: Reference for structured dialogue design and future adapter experiments.
- access/license: public: Check repository license and data terms.
- downloaded locally: `false`
- limitations: Synthetic task orientation differs from real friction-heavy business conversations.

#### Taskmaster-3
- type: `dataset`
- modality: `transcript`
- source: https://ai.google.com/research/Datasets/Taskmaster
- relevance: Multi-turn task-oriented dialogue reference with transactional structure closer to support and sales workflows.
- recommended use: Reference for future multi-turn support/sales benchmarking or schema design.
- access/license: public: Review Google dataset terms before use.
- downloaded locally: `false`
- limitations: Task-completion success is not the same as escalation, uncertainty, or pricing friction review.
