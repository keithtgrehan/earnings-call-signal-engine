# Dataset and Research Map

This map extends the transcript-first research manifest into audio, video, and multimodal references without changing canonical scoring.

- generated_at: `2026-04-24T17:36:48+00:00`
- entry_count: `35`
- canonical path: transcript-first deterministic extraction
- optional layers: audio/video review cues, benchmark-only adapters, later fusion experiments

## Limitations

- Transcript-first deterministic outputs remain canonical.
- Audio and video sources are benchmark and review-cue references only.
- Several datasets are gated or license-restricted and are intentionally documented without local download.

## Transcript Sources

### ICSI Meeting Recorder Dialog Act Corpus (MRDA)
- id: `mrda`
- type: `dataset`
- category: `dialogue_acts`
- url: https://catalog.ldc.upenn.edu/LDC2004T12
- relevance: Useful reference for meeting-style dialogue acts, interruptions, and conversational structure.
- labels/features: statement, question, floor management, disruption cues
- access: `license_required`
- license notes: LDC access required.
- download status: `not_downloaded`
- recommended use: Methodology reference for dialogue-act framing and annotation guidelines.
- limitations: Meeting domain differs materially from support, sales, and earnings calls.

### Switchboard Dialog Act Corpus
- id: `switchboard_dialog_act_corpus`
- type: `dataset`
- category: `dialogue_acts`
- url: https://catalog.ldc.upenn.edu/LDC97S62
- relevance: Classic dialogue-act resource for Q&A turn structure, directness, and conversational move design.
- labels/features: statement, question, backchannel, opinion, agreement
- access: `license_required`
- license notes: LDC access required.
- download status: `not_downloaded`
- recommended use: Taxonomy and methodology reference; document metadata only unless licensed access is available.
- limitations: License-gated and not finance-specific.

### Aiera/aiera-transcript-sentiment dataset
- id: `aiera_transcript_sentiment`
- type: `dataset`
- category: `earnings_calls`
- url: https://huggingface.co/datasets/Aiera/aiera-transcript-sentiment
- relevance: Potential finance transcript sentiment benchmark candidate closer to earnings-call language than generic emotion corpora.
- labels/features: transcript sentiment labels, finance text classification
- access: `public`
- license notes: Review dataset card before use.
- download status: `not_downloaded`
- recommended use: Optional benchmark reference only; do not vendor without checking terms.
- limitations: Sentiment labels alone still under-specify guidance change, pressure, and evidence quality.

### Forecasting Earnings Surprises from Conference Call Transcripts
- id: `forecasting_earnings_surprises`
- type: `paper`
- category: `earnings_calls`
- url: https://aclanthology.org/2023.findings-acl.520/
- relevance: Strong earnings-call NLP reference tying transcript content to future surprise prediction tasks.
- labels/features: earnings surprise direction, transcript segmentation, finance text modeling
- access: `public`
- license notes: Public paper; datasets may have separate access terms.
- download status: `not_downloaded`
- recommended use: Research reference only for benchmark framing and task design, not for unsupported performance claims.
- limitations: Prediction framing is narrower and higher-risk than the repo's deterministic review focus.

### jlh-ibm/earnings_call dataset
- id: `ibm_earnings_call_dataset`
- type: `dataset`
- category: `earnings_calls`
- url: https://huggingface.co/datasets/jlh-ibm/earnings_call
- relevance: Useful reference source for transcript structure and later optional finance-language benchmarking.
- labels/features: earnings call transcripts, Q&A sections, firm/date metadata
- access: `public`
- license notes: Check dataset card and underlying transcript rights before local use.
- download status: `not_downloaded`
- recommended use: Metadata/reference only unless licensing is explicitly acceptable for local experiments.
- limitations: Transcript rights and reuse terms may limit direct training use.

### Modeling financial analysts' decision making via the pragmatics and semantics of earnings calls
- id: `earnings_calls_analyst_decision_making`
- type: `paper`
- category: `earnings_calls`
- url: https://arxiv.org/abs/1906.02868
- relevance: Directly relevant to analyst pressure, Q&A pragmatics, and post-call interpretation features.
- labels/features: question pragmatics, semantics, analyst behavior, forecast revision correlates
- access: `public`
- license notes: Public paper.
- download status: `not_downloaded`
- recommended use: Research reference for transcript features around analyst-management friction and Q&A pressure.
- limitations: Research correlations are not a license to claim predictive lift in this portfolio project.

### Predicting Corporate Risk by Jointly Modeling Company Networks and Dialogues in Earnings Conference Calls
- id: `predicting_corporate_risk_dialogues`
- type: `paper`
- category: `earnings_calls`
- url: https://arxiv.org/abs/2206.06174
- relevance: Relevant to dialogue-aware modeling and the limits of transcript-only risk inference.
- labels/features: dialogue structure, corporate risk, company network context
- access: `public`
- license notes: Public paper.
- download status: `not_downloaded`
- recommended use: Reference for future optional benchmark design around dialogue structure and risk cues.
- limitations: Modeling setup is more ambitious than the current deterministic-first architecture.

### SubjECTive-QA: Measuring Subjectivity in Earnings Call Transcripts' QA Through Six-Dimensional Feature Analysis
- id: `subjective_qa`
- type: `paper`
- category: `earnings_calls`
- url: https://arxiv.org/abs/2410.20651
- relevance: Highly aligned with bounded review cues for subjectivity, uncertainty, and question-answer quality.
- labels/features: subjectivity dimensions, question-answer analysis, explainable features
- access: `public`
- license notes: Public paper.
- download status: `not_downloaded`
- recommended use: Reference for future bounded QA-review taxonomies without turning subjectivity into canonical truth.
- limitations: Published methodology still needs careful translation into reviewer-centric signals.

### EmpatheticDialogues
- id: `empathetic_dialogues`
- type: `dataset`
- category: `emotion_uncertainty`
- url: https://arxiv.org/abs/1811.00207
- relevance: Relevant as a contrastive dialogue corpus for empathy-like language, but not a direct fit for deterministic business review.
- labels/features: emotion situations, empathetic response generation
- access: `public`
- license notes: Dataset reuse depends on release terms.
- download status: `not_downloaded`
- recommended use: Reference only for future dialogue-style experiments, not as a direct product dataset.
- limitations: Empathy generation is far from earnings-call or support-ops review workflows.

### GoEmotions
- id: `goemotions`
- type: `dataset`
- category: `emotion_uncertainty`
- url: https://arxiv.org/abs/2005.00547
- relevance: Useful for optional fine-grained emotion benchmarking, especially as a contrast to business-domain signals.
- labels/features: fine-grained emotion classes, neutral
- access: `public`
- license notes: Paper is public; dataset terms should be reviewed before local download.
- download status: `not_downloaded`
- recommended use: Benchmark reference for optional text-emotion experiments only.
- limitations: Reddit emotion labels are not the same thing as business-review signals or internal state.

### Financial PhraseBank
- id: `financial_phrasebank`
- type: `dataset`
- category: `financial_nlp`
- url: https://huggingface.co/datasets/takala/financial_phrasebank
- relevance: Widely used sentence-level finance sentiment dataset that grounds benchmark comparisons for finance text.
- labels/features: positive, neutral, negative financial sentiment
- access: `public`
- license notes: Dataset card should be reviewed before redistribution or bulk download.
- download status: `not_downloaded`
- recommended use: Benchmark-only sentiment reference; useful for checking whether optional models behave sensibly on finance language.
- limitations: Short isolated sentences are a weak proxy for multi-speaker transcript review.

### FinBERT: Financial Sentiment Analysis with Pre-trained Language Models
- id: `finbert_paper`
- type: `paper`
- category: `financial_nlp`
- url: https://arxiv.org/abs/1908.10063
- relevance: Strong finance-domain baseline reference for sentence-level sentiment benchmarking on financial text.
- labels/features: positive, negative, neutral financial sentiment
- access: `public`
- license notes: Paper is public; model and downstream datasets have separate licenses.
- download status: `not_downloaded`
- recommended use: Reference model family for optional benchmark comparisons against deterministic transcript signals.
- limitations: Sentiment labels do not map directly to guidance change, friction, or evidence quality.

### FinNLI: Novel Dataset for Multi-Genre Financial Natural Language Inference Benchmarking
- id: `finnli_dataset`
- type: `dataset`
- category: `financial_nlp`
- url: https://arxiv.org/abs/2504.16188
- relevance: Useful for reasoning-style benchmark planning around contradiction, entailment, and guidance language review.
- labels/features: entailment, contradiction, neutral
- access: `public`
- license notes: Check dataset release terms before local use.
- download status: `not_downloaded`
- recommended use: Reference for optional contradiction and disclosure-consistency experiments.
- limitations: NLI labels do not directly validate reviewer usefulness in business-conversation workflows.

### FiQA benchmark
- id: `fiqa_benchmark`
- type: `benchmark`
- category: `financial_nlp`
- url: https://sites.google.com/view/fiqa/
- relevance: Finance QA and sentiment benchmark reference for optional retrieval and finance-language experiments.
- labels/features: financial sentiment, question answering, ranking
- access: `public`
- license notes: Benchmark access and downstream dataset terms should be reviewed case by case.
- download status: `not_downloaded`
- recommended use: Reference only for optional finance retrieval and question-answer benchmarking.
- limitations: FiQA is not an earnings-call review dataset and does not validate conversation-level evidence quality.

### Loughran-McDonald Master Dictionary
- id: `loughran_mcdonald_dictionary`
- type: `library`
- category: `financial_nlp`
- url: https://sraf.nd.edu/loughranmcdonald-master-dictionary/
- relevance: Finance-specific lexicon reference for uncertainty and tone features without requiring black-box models.
- labels/features: negative, positive, uncertainty, litigious, strong_modal, weak_modal
- access: `public`
- license notes: Review site terms before vendoring any dictionary files.
- download status: `not_downloaded`
- recommended use: Lexicon reference for deterministic or weak-label experiments on earnings-call language.
- limitations: Dictionary counts need careful context handling and can overfire on long transcripts.

### ProsusAI/finbert model card
- id: `prosus_finbert_model`
- type: `library`
- category: `financial_nlp`
- url: https://huggingface.co/ProsusAI/finbert
- relevance: Concrete local-model candidate for optional finance-specific benchmarking when cache is already available.
- labels/features: financial sentiment classification pipeline
- access: `public`
- license notes: Use subject to model card and underlying dataset terms.
- download status: `not_downloaded`
- recommended use: Optional offline benchmark adapter only; not canonical scoring.
- limitations: Model-card availability does not guarantee local model cache or fit for earnings-call Q&A nuance.

### scikit-learn
- id: `scikit_learn`
- type: `library`
- category: `libraries`
- url: https://scikit-learn.org/stable/
- relevance: Lightweight baseline-training stack for TF-IDF and classical classifiers without heavyweight models.
- labels/features: TF-IDF, LogisticRegression, LinearSVC, calibration, metrics
- access: `public`
- license notes: BSD-style open source license.
- download status: `not_downloaded`
- recommended use: Use for weak-label baselines and benchmark scaffolding only.
- limitations: Classical text baselines depend heavily on label quality and task framing.

### spaCy
- id: `spacy`
- type: `library`
- category: `libraries`
- url: https://spacy.io/
- relevance: Useful optional library for tokenization, pattern matching, and lightweight rule-based NLP workflows.
- labels/features: tokenization, dependency patterns, named entities, custom rule pipelines
- access: `public`
- license notes: See spaCy license and model-specific terms.
- download status: `not_downloaded`
- recommended use: Optional support library for deterministic extraction and offline preprocessing.
- limitations: Library support alone does not create validated business-review signals.

### BANKING77
- id: `banking77`
- type: `dataset`
- category: `support_sales`
- url: https://huggingface.co/datasets/PolyAI/banking77
- relevance: Good intent-detection reference for finance-adjacent customer requests and support language.
- labels/features: banking intents, complaint categories, support actions
- access: `public`
- license notes: Review dataset card before local use.
- download status: `not_downloaded`
- recommended use: Benchmark reference for narrow-domain intent classification, especially support-style queries.
- limitations: Short user requests do not capture multi-turn review dynamics.

### CLINC150
- id: `clinc150`
- type: `dataset`
- category: `support_sales`
- url: https://archive.ics.uci.edu/ml/datasets/CLINC150
- relevance: Intent classification baseline reference for weak-label or synthetic intent experiments.
- labels/features: intent classes, out-of-scope detection
- access: `public`
- license notes: Use subject to UCI and original dataset terms.
- download status: `not_downloaded`
- recommended use: Reference for intent taxonomy design and robustness checks.
- limitations: Assistant-intent framing does not directly capture escalation, evidence, or reviewer usefulness.

### Schema-Guided Dialogue dataset
- id: `schema_guided_dialogue`
- type: `dataset`
- category: `support_sales`
- url: https://github.com/google-research-datasets/dstc8-schema-guided-dialogue
- relevance: Useful for slot/intent-oriented customer-service dialogue structure and domain-transfer thinking.
- labels/features: intent, slot, dialogue state, multi-domain service interactions
- access: `public`
- license notes: Check repository license and data terms.
- download status: `not_downloaded`
- recommended use: Reference for structured dialogue design and future adapter experiments.
- limitations: Synthetic task orientation differs from real friction-heavy business conversations.

### Taskmaster-3
- id: `taskmaster3`
- type: `dataset`
- category: `support_sales`
- url: https://ai.google.com/research/Datasets/Taskmaster
- relevance: Multi-turn task-oriented dialogue reference with transactional structure closer to support and sales workflows.
- labels/features: task completion, intents, entity slots, follow-up commitments
- access: `public`
- license notes: Review Google dataset terms before use.
- download status: `not_downloaded`
- recommended use: Reference for future multi-turn support/sales benchmarking or schema design.
- limitations: Task-completion success is not the same as escalation, uncertainty, or pricing friction review.


## Audio Sources

### CREMA-D
- id: `crema_d`
- type: `dataset`
- category: `audio`
- url: https://huggingface.co/datasets/AbstractTTS/CREMA-D
- relevance: Speech emotion reference corpus for optional audio benchmarking.
- labels/features: emotion category, intensity, acted speech audio
- access: `public`
- license notes: Check dataset card and original release terms.
- download status: `not_downloaded`
- recommended use: Benchmark reference only.
- limitations: Acted performances can overstate how separable real-world cues are.

### IEMOCAP
- id: `iemocap`
- type: `dataset`
- category: `audio`
- url: https://sail.usc.edu/iemocap/
- relevance: Widely cited speech-emotion dataset with multimodal components.
- labels/features: emotion labels, audio, video, transcripts
- access: `license_required`
- license notes: Registration and dataset agreement required.
- download status: `not_downloaded`
- recommended use: Metadata and evaluation reference only unless access is approved.
- limitations: Access-restricted and still based on acted or semi-scripted interactions.

### librosa
- id: `librosa`
- type: `library`
- category: `audio`
- url: https://librosa.org/
- relevance: Flexible Python audio analysis toolkit for lightweight offline feature extraction.
- labels/features: duration, RMS energy, tempo proxies, silence proxies, spectral features
- access: `public`
- license notes: Open source library; see project license.
- download status: `not_downloaded`
- recommended use: Optional bounded audio feature extraction when local audio is available.
- limitations: Speech-specific interpretation still requires careful framing and validation.

### MSP-Podcast
- id: `msp_podcast`
- type: `dataset`
- category: `audio`
- url: https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html
- relevance: Important benchmark reference for more naturalistic speech emotion work.
- labels/features: emotion labels, activation, valence, speech segments
- access: `license_required`
- license notes: Access terms should be reviewed before use.
- download status: `not_downloaded`
- recommended use: Benchmark reference for later audio-sidecar evaluation design.
- limitations: Still not a direct business-conversation review corpus.

### openSMILE
- id: `opensmile`
- type: `library`
- category: `audio`
- url: https://audeering.github.io/opensmile-python/
- relevance: Classic handcrafted audio-feature extractor for bounded prosody experiments.
- labels/features: MFCCs, loudness, pitch, spectral descriptors, eGeMAPS
- access: `public`
- license notes: Review library and feature-set licensing before commercial use.
- download status: `not_downloaded`
- recommended use: Optional benchmark-only audio feature extraction.
- limitations: Prosody features are review cues, not internal-state truth.

### pyannote.audio
- id: `pyannote_audio`
- type: `tool`
- category: `audio`
- url: https://github.com/pyannote/pyannote-audio
- relevance: Strong diarization/VAD option for future audio sidecars when licensed and cached locally.
- labels/features: speaker diarization, voice activity detection, segmentation
- access: `public`
- license notes: Review repository, model, and Hugging Face token requirements before use.
- download status: `not_downloaded`
- recommended use: Optional future adapter for diarization and speaker-turn recovery.
- limitations: Often requires model downloads and tokens; not suitable for lightweight default CI.

### RAVDESS
- id: `ravdess`
- type: `dataset`
- category: `audio`
- url: https://zenodo.org/records/1188976
- relevance: Common audio emotion benchmark reference for prosody experiments.
- labels/features: speech emotion, song emotion, intensity
- access: `public`
- license notes: Review dataset terms before use.
- download status: `not_downloaded`
- recommended use: Benchmark reference only for optional speech-emotion sidecars.
- limitations: Acted emotion data is a poor proxy for real business conversations.


## Video Sources

### Aff-Wild2
- id: `aff_wild2`
- type: `benchmark`
- category: `video`
- url: https://ibug.doc.ic.ac.uk/resources/aff-wild2/
- relevance: High-visibility facial-behavior benchmark reference for documenting what remains optional and access-constrained.
- labels/features: valence-arousal, action units, expression, head pose
- access: `license_required`
- license notes: Registration and benchmark access restrictions apply.
- download status: `not_downloaded`
- recommended use: Metadata-only reference unless access is explicitly approved.
- limitations: Benchmark framing can easily be overinterpreted; keep it out of canonical review logic.

### MediaPipe
- id: `mediapipe`
- type: `tool`
- category: `video`
- url: https://developers.google.com/mediapipe
- relevance: Optional local landmark and pose toolkit for bounded escalation-only video cues.
- labels/features: face landmarks, pose, hands, tracking
- access: `public`
- license notes: See MediaPipe terms and model licenses.
- download status: `not_downloaded`
- recommended use: Optional enhancement for local face-visibility and motion proxies on escalated cases.
- limitations: Landmarks are not emotion truth and should stay secondary to transcript evidence.

### OpenCV
- id: `opencv`
- type: `library`
- category: `video`
- url: https://opencv.org/
- relevance: Lightweight frame-level statistics, motion proxies, and quality checks for optional video sidecars.
- labels/features: frame count, fps, brightness stats, motion proxy, detection utilities
- access: `public`
- license notes: Open source library; see project license.
- download status: `not_downloaded`
- recommended use: Optional bounded preprocessing for video quality and motion cues.
- limitations: Generic CV features do not justify body-language certainty claims.


## Multimodal Sources

### CMU-MOSEI
- id: `cmu_mosei`
- type: `dataset`
- category: `multimodal`
- url: http://multicomp.cs.cmu.edu/resources/cmu-mosei-dataset/
- relevance: Large multimodal sentiment and emotion benchmark reference for future evaluation design.
- labels/features: sentiment, emotion, aligned text/audio/video
- access: `public`
- license notes: Review dataset terms before use.
- download status: `not_downloaded`
- recommended use: Methodology reference for multimodal alignment and benchmark protocol design.
- limitations: General web-video sentiment is still far from earnings-call or support-review settings.

### CMU-MOSI
- id: `cmu_mosi`
- type: `dataset`
- category: `multimodal`
- url: http://multicomp.cs.cmu.edu/resources/cmu-mosi-dataset/
- relevance: Classic multimodal sentiment benchmark for text-audio-visual fusion references.
- labels/features: opinion sentiment, aligned text/audio/video segments
- access: `public`
- license notes: Review dataset terms before download or reuse.
- download status: `not_downloaded`
- recommended use: Benchmark methodology reference for late-fusion planning.
- limitations: Opinion videos are not business-review transcripts.

### MELD
- id: `meld`
- type: `dataset`
- category: `multimodal`
- url: https://github.com/declare-lab/MELD
- relevance: Conversation-level multimodal emotion benchmark reference with speaker turns.
- labels/features: emotion, sentiment, dialogue turns, audio-video alignment
- access: `public`
- license notes: Review repository and upstream media terms.
- download status: `not_downloaded`
- recommended use: Reference for conversational multimodal evaluation design only.
- limitations: TV-dialogue emotion labels do not establish reviewer usefulness in business calls.
