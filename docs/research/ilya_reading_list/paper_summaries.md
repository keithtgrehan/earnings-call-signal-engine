# Paper Summaries

Each item separates researched/distilled knowledge from implementation claims. No paper below is claimed as implemented in Signal Engine 2.0.

## The First Law of Complexodynamics

- ID: `first_law_complexodynamics`
- Authors: Scott Aaronson
- Year: 2011
- Category: `compression_mdl_complexity`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://scottaaronson.blog/?p=762

### Core Idea

Complexity can rise and fall even while entropy rises monotonically; interesting structure may peak between order and randomness.

### Why It Mattered Historically

It connects thermodynamics, algorithmic information, and a practical intuition behind why the middle of a system evolution can be most informative.

### Key Technical Concepts

- Kolmogorov complexity
- sophistication
- entropy vs complexity
- resource-bounded description length

### What A Beginner Should Understand

A sequence is not useful just because it is random or long; useful structure often lives in compressible-but-not-trivial patterns.

### What Matters For Signal Engine 2.0

- Frame transcript signals as patterns between randomness and over-simple keyword rules
- Use compression-style diagnostics to spot boilerplate vs information-rich sections

### Possible Feature Ideas

- Compression ratio feature for prepared remarks vs Q&A
- Novelty/boilerplate score for management language
- Complexity-over-call timeline

### Possible Evaluation Ideas

- Compare compression/novelty scores against human evidence-span labels
- Check whether high-complexity Q&A spans correlate with analyst pressure labels

### Risks / Limitations

- Conceptual blog post, not an NLP model
- Compression proxies can confuse topic shifts with meaningful complexity

## The Unreasonable Effectiveness of Recurrent Neural Networks

- ID: `unreasonable_effectiveness_rnns`
- Authors: Andrej Karpathy
- Year: 2015
- Category: `sequence_models`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://karpathy.github.io/2015/05/21/rnn-effectiveness/

### Core Idea

Small recurrent models can learn surprising local and long-range structure from raw sequences.

### Why It Mattered Historically

It helped make sequence learning tangible and showed that raw text modeling could reveal structure without heavy feature engineering.

### Key Technical Concepts

- RNN
- character-level language modeling
- hidden state
- sequence generation

### What A Beginner Should Understand

RNNs process one step at a time while carrying a hidden state, so they are a natural first mental model for transcript sequences.

### What Matters For Signal Engine 2.0

- Motivates transcript-first sequence modeling before heavy architectures
- Supports section-aware modeling of prepared remarks and Q&A

### Possible Feature Ideas

- Character/word baseline language model probes
- Sequence continuity checks
- Transcript anomaly examples for demos

### Possible Evaluation Ideas

- Train tiny local baselines only after enough transcripts
- Evaluate generated/next-token probes as diagnostics, not product claims

### Risks / Limitations

- Blog/demo evidence is not domain validation
- RNNs are mostly a historical baseline for modern transformer work

## Understanding LSTM Networks

- ID: `understanding_lstm_networks`
- Authors: Christopher Olah
- Year: 2015
- Category: `sequence_models`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://colah.github.io/posts/2015-08-Understanding-LSTMs/, https://research.google/pubs/understanding-lstm-networks/

### Core Idea

LSTMs use gated memory to preserve and update information across long sequences.

### Why It Mattered Historically

It became one of the clearest explanations of why gated recurrent units solved practical long-dependency problems.

### Key Technical Concepts

- LSTM
- gates
- cell state
- long-term dependencies
- GRU

### What A Beginner Should Understand

The cell state is a controlled memory path; gates decide what to keep, forget, and expose.

### What Matters For Signal Engine 2.0

- Clarifies why long earnings calls need memory over many turns
- Gives vocabulary for modeling guidance setup and later Q&A follow-through

### Possible Feature Ideas

- Section memory features
- Long-range callback detector
- Guidance mention carry-forward map

### Possible Evaluation Ideas

- Check whether later Q&A references earlier prepared remarks
- Measure section-aware recall in retrieval baselines

### Risks / Limitations

- Tutorial, not a benchmark
- Modern systems usually use transformers but still face memory-window design problems

## Recurrent Neural Network Regularization

- ID: `rnn_regularization`
- Authors: Wojciech Zaremba, Ilya Sutskever, Oriol Vinyals
- Year: 2014
- Category: `sequence_models`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1409.2329

### Core Idea

Dropout can regularize LSTMs when applied to non-recurrent connections while preserving recurrent memory.

### Why It Mattered Historically

It made LSTM language models more reliable and practical across NLP, speech, translation, and captioning tasks.

### Key Technical Concepts

- dropout
- LSTM regularization
- overfitting
- non-recurrent connections

### What A Beginner Should Understand

Regularization is not an afterthought; how it is applied must respect the model architecture.

### What Matters For Signal Engine 2.0

- Warns that transcript models will overfit small corpora without disciplined regularization
- Useful for 30/100/500 transcript model gating

### Possible Feature Ideas

- Regularized local baseline checklist
- Overfit warning report for optional classifiers

### Possible Evaluation Ideas

- Track train/dev gap by transcript count
- Require held-out-call performance before promoting any learned model

### Risks / Limitations

- Small finance corpora are especially overfit-prone
- Paper does not remove need for careful labels

## Keeping Neural Networks Simple by Minimizing the Description Length of the Weights

- ID: `keeping_neural_networks_simple_mdl_weights`
- Authors: Geoffrey E. Hinton, Drew van Camp
- Year: 1993
- Category: `compression_mdl_complexity`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://www.cs.toronto.edu/~hinton/absps/colt93.html

### Core Idea

A neural network should balance fit with the amount of information needed to describe its weights.

### Why It Mattered Historically

It is an early bridge between neural network regularization and information-theoretic model selection.

### Key Technical Concepts

- minimum description length
- weight noise
- regularization
- model simplicity

### What A Beginner Should Understand

A model that memorizes is expensive to describe; simplicity can be a guardrail against fake performance.

### What Matters For Signal Engine 2.0

- Supports simple, auditable baselines before complex ML
- Provides theory for penalizing over-complex transcript models

### Possible Feature Ideas

- Model complexity budget
- Baseline selection rubric
- Description-length-inspired error analysis

### Possible Evaluation Ideas

- Compare simple deterministic features to optional learned baselines
- Track performance per model-complexity tier

### Risks / Limitations

- Historical method, not directly implemented
- MDL approximations can be hard to explain to nontechnical users

## Pointer Networks

- ID: `pointer_networks`
- Authors: Oriol Vinyals, Meire Fortunato, Navdeep Jaitly
- Year: 2015
- Category: `attention_transformers`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1506.03134

### Core Idea

Attention can act as a pointer over input positions, enabling variable-size outputs tied directly to the input.

### Why It Mattered Historically

It showed attention was more than soft context; it could select structured outputs from an input sequence.

### Key Technical Concepts

- pointer attention
- variable output dictionary
- combinatorial optimization
- sequence-to-sequence

### What A Beginner Should Understand

Some tasks should not generate labels from nowhere; they should point to the evidence that justifies them.

### What Matters For Signal Engine 2.0

- Maps neatly to evidence-span selection where outputs point back to transcript positions
- Informs extractive citation-first interfaces

### Possible Feature Ideas

- Pointer-style evidence selector
- Quote span candidate ranker
- Transcript segment pointer UI

### Possible Evaluation Ideas

- Evidence-span precision/recall
- Reviewer agreement on selected transcript spans

### Risks / Limitations

- Do not claim neural pointer networks are implemented
- Pointer ideas require gold spans to evaluate properly

## ImageNet Classification with Deep Convolutional Neural Networks

- ID: `imagenet_classification_deep_cnn`
- Authors: Alex Krizhevsky, Ilya Sutskever, Geoffrey E. Hinton
- Year: 2012
- Category: `vision_multimodal`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks.pdf

### Core Idea

A large CNN trained with GPUs and practical tricks dramatically improved ImageNet classification.

### Why It Mattered Historically

AlexNet marked the deep learning breakthrough moment for large-scale computer vision.

### Key Technical Concepts

- CNN
- ReLU
- GPU training
- dropout
- data augmentation
- ImageNet

### What A Beginner Should Understand

Architecture matters, but the win came from model, data, compute, and evaluation all lining up.

### What Matters For Signal Engine 2.0

- Sets expectations for data scale and benchmark rigor before multimodal claims
- Useful historical anchor for future visual status/audio-video work

### Possible Feature Ideas

- Visual frame feature candidate registry
- Multimodal benchmark readiness checklist

### Possible Evaluation Ideas

- Only evaluate visual features when source coverage and labels exist
- Compare text-only vs text+media lift on fixed cases

### Risks / Limitations

- Image classification is far from earnings-call understanding
- GPU-heavy training is out of scope now

## Order Matters: Sequence to Sequence for Sets

- ID: `order_matters_seq2seq_sets`
- Authors: Oriol Vinyals, Samy Bengio, Manjunath Kudlur
- Year: 2015
- Category: `sequence_models`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1511.06391

### Core Idea

Sequence models can be sensitive to arbitrary input/output order when representing sets.

### Why It Mattered Historically

It clarified a subtle weakness in applying sequence tools to unordered objects.

### Key Technical Concepts

- sets
- sequence ordering
- attention
- permutation sensitivity

### What A Beginner Should Understand

Before feeding data to a model, ask whether the order is real signal or an accidental artifact.

### What Matters For Signal Engine 2.0

- Important for transcript chunks: some order is meaningful, some candidate sets need order-invariant treatment
- Guides chunk ordering experiments

### Possible Feature Ideas

- Permutation stress test for chunk rankers
- Set-vs-sequence evaluation mode

### Possible Evaluation Ideas

- Shuffle candidate evidence spans and measure stability
- Compare chronological vs relevance-sorted retrieval contexts

### Risks / Limitations

- Not a direct earnings-call model
- Order invariance can remove useful chronology if applied carelessly

## GPipe: Easy Scaling with Micro-Batch Pipeline Parallelism

- ID: `gpipe_scaling_microbatch_pipeline_parallelism`
- Authors: Yanping Huang, Youlong Cheng, Ankur Bapna, Orhan Firat, Dehao Chen, Mia Chen, HyoukJoong Lee, Jiquan Ngiam, Quoc V. Le, Yonghui Wu, Zhifeng Chen
- Year: 2018
- Category: `scaling_systems`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1811.06965

### Core Idea

Large neural networks can be split across accelerators and trained efficiently with micro-batch pipeline parallelism.

### Why It Mattered Historically

It helped make model-parallel training more accessible for giant networks.

### Key Technical Concepts

- pipeline parallelism
- micro-batching
- model partitioning
- large model training

### What A Beginner Should Understand

Scaling systems work is valuable, but it only matters after the task, labels, and metrics are worth scaling.

### What Matters For Signal Engine 2.0

- Roadmap reference only: Signal Engine should scale data and evaluation before training large models
- Informs future remote/GPU planning

### Possible Feature Ideas

- Compute readiness checklist
- Training escalation gates
- Optional large-model experiment plan

### Possible Evaluation Ideas

- Record cost/performance only after local baselines saturate
- Gate GPU work on benchmark stability

### Risks / Limitations

- Out of scope for current repo behavior
- Could encourage premature infrastructure work

## Deep Residual Learning for Image Recognition

- ID: `deep_residual_learning_image_recognition`
- Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
- Year: 2015
- Category: `vision_multimodal`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1512.03385

### Core Idea

Residual connections let very deep networks learn refinements over identity mappings.

### Why It Mattered Historically

ResNet made extremely deep networks trainable and became a backbone for vision and beyond.

### Key Technical Concepts

- residual connections
- skip connections
- deep CNNs
- gradient flow

### What A Beginner Should Understand

Sometimes the best module learns a correction to a reliable baseline rather than replacing it.

### What Matters For Signal Engine 2.0

- Residual thinking maps to additive signal layers that do not erase deterministic baselines
- Useful analogy for modular architecture

### Possible Feature Ideas

- Additive evidence scoring layers
- Residual-style model sidecars that preserve deterministic output

### Possible Evaluation Ideas

- Ablate each sidecar as a residual contribution
- Measure lift over deterministic baseline, not standalone score only

### Risks / Limitations

- Architecture analogy should not be overclaimed
- Vision results do not prove transcript behavior

## Multi-Scale Context Aggregation by Dilated Convolutions

- ID: `multi_scale_context_aggregation_dilated_convolutions`
- Authors: Fisher Yu, Vladlen Koltun
- Year: 2015
- Category: `vision_multimodal`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1511.07122

### Core Idea

Dilated convolutions expand context without reducing resolution.

### Why It Mattered Historically

It influenced dense prediction models by showing how to aggregate broader context efficiently.

### Key Technical Concepts

- dilated convolutions
- multi-scale context
- receptive field
- semantic segmentation

### What A Beginner Should Understand

A signal engine needs both the exact sentence and the surrounding call context.

### What Matters For Signal Engine 2.0

- Inspires multi-window transcript context features without losing local evidence resolution
- Useful for hierarchical section/chunk analysis

### Possible Feature Ideas

- Local/medium/global transcript window features
- Evidence span context ladder

### Possible Evaluation Ideas

- Compare single-sentence vs neighboring-window evidence quality
- Measure context window impact on false positives

### Risks / Limitations

- CNN mechanism is not directly used
- Wide context can dilute evidence if not evaluated

## Neural Message Passing for Quantum Chemistry

- ID: `neural_message_passing_quantum_chemistry`
- Authors: Justin Gilmer, Samuel S. Schoenholz, Patrick F. Riley, Oriol Vinyals, George E. Dahl
- Year: 2017
- Category: `graph_relational_learning`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1704.01212, https://research.google/pubs/neural-message-passing-for-quantum-chemistry/

### Core Idea

Graph neural networks can be described through message, update, and readout steps over structured objects.

### Why It Mattered Historically

It unified several graph neural approaches and accelerated graph learning as a general framework.

### Key Technical Concepts

- message passing neural networks
- graphs
- node updates
- readout functions

### What A Beginner Should Understand

When the data is relationships rather than a flat string, graph structure can make the task clearer.

### What Matters For Signal Engine 2.0

- Maps to speaker-turn graphs, analyst/company interaction networks, and cross-call entity relations
- Useful for future relational transcript intelligence

### Possible Feature Ideas

- Speaker-turn graph scaffold
- Question-answer relation graph
- Company/topic graph features

### Possible Evaluation Ideas

- Evaluate graph features against Q&A friction labels
- Ablate speaker/entity edges from retrieval

### Risks / Limitations

- Chemistry benchmark does not transfer directly
- Graph construction can inject subjective assumptions

## Attention Is All You Need

- ID: `attention_is_all_you_need`
- Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin
- Year: 2017
- Category: `attention_transformers`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1706.03762

### Core Idea

Self-attention can replace recurrence/convolution for sequence transduction and scale efficiently in parallel.

### Why It Mattered Historically

The Transformer became the foundation for modern LLMs and most current NLP systems.

### Key Technical Concepts

- self-attention
- Transformer
- multi-head attention
- positional encoding
- encoder-decoder

### What A Beginner Should Understand

Attention lets each token condition on other relevant tokens, but position and context design still matter.

### What Matters For Signal Engine 2.0

- Core mental model for retrieval, reranking, long-context transcript analysis, and future transformer baselines
- Guides attention-inspired evidence weighting

### Possible Feature Ideas

- Attention-inspired chunk reranker
- Transformer baseline experiment
- Long-context evidence packing strategy

### Possible Evaluation Ideas

- Compare lexical retrieval vs embedding/reranker candidates
- Measure evidence citation quality and section recall

### Risks / Limitations

- Do not imply a transformer is implemented here
- Attention maps are not automatically explanations

## Neural Machine Translation by Jointly Learning to Align and Translate

- ID: `nmt_jointly_learning_align_translate`
- Authors: Dzmitry Bahdanau, Kyunghyun Cho, Yoshua Bengio
- Year: 2014
- Category: `attention_transformers`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1409.0473

### Core Idea

A translation decoder can softly search source positions instead of relying on one fixed-length context vector.

### Why It Mattered Historically

It introduced neural attention in a form that reshaped sequence modeling.

### Key Technical Concepts

- attention
- alignment
- encoder-decoder
- soft search

### What A Beginner Should Understand

For any output claim, the model should know where it looked in the input.

### What Matters For Signal Engine 2.0

- Directly relevant to aligning extracted signals with source transcript evidence
- Pre-transformer foundation for evidence-aware modeling

### Possible Feature Ideas

- Signal-to-evidence alignment report
- Attention-style quote support scoring

### Possible Evaluation Ideas

- Gold evidence alignment precision
- Long-section degradation tests

### Risks / Limitations

- Translation alignment is not identical to financial signal evidence
- Soft attention is not a human-readable proof by itself

## Identity Mappings in Deep Residual Networks

- ID: `identity_mappings_deep_residual_networks`
- Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
- Year: 2016
- Category: `representation_learning`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1603.05027

### Core Idea

Clean identity paths improve optimization in deep residual networks.

### Why It Mattered Historically

It refined ResNet design and reinforced the importance of information-preserving paths.

### Key Technical Concepts

- identity skip connections
- pre-activation ResNet
- gradient propagation

### What A Beginner Should Understand

A system should keep a reliable path for original information while layers add value.

### What Matters For Signal Engine 2.0

- Architectural lesson for sidecars: preserve the base transcript object and add refinements
- Supports non-destructive feature composition

### Possible Feature Ideas

- Non-destructive scoring pipeline notes
- Sidecar ablation protocol

### Possible Evaluation Ideas

- Verify sidecars never remove source evidence
- Measure each layer as incremental lift

### Risks / Limitations

- Analogy only unless a neural model is later built
- Architecture details are vision-specific

## A Simple Neural Network Module for Relational Reasoning

- ID: `simple_module_relational_reasoning`
- Authors: Adam Santoro, David Raposo, David G. T. Barrett, Mateusz Malinowski, Razvan Pascanu, Peter Battaglia, Timothy Lillicrap
- Year: 2017
- Category: `graph_relational_learning`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1706.01427

### Core Idea

A simple module can reason over pairs of objects by aggregating learned relation functions.

### Why It Mattered Historically

It showed that explicit relational modules can solve tasks standard networks miss.

### Key Technical Concepts

- relation networks
- object pairs
- relational reasoning
- visual question answering

### What A Beginner Should Understand

Some questions are about relationships, not isolated objects or sentences.

### What Matters For Signal Engine 2.0

- Useful for modeling relations across speaker turns, analyst questions, management answers, and entities
- Highlights relation-specific evaluation needs

### Possible Feature Ideas

- Speaker relation features
- Question-answer consistency checker
- Entity relation evidence table

### Possible Evaluation Ideas

- Evaluate whether answer-evasion labels improve with Q/A pair features
- Test relation features on analyst pressure examples

### Risks / Limitations

- Synthetic visual tasks differ from earnings calls
- Relation extraction can create brittle pair explosions

## Variational Lossy Autoencoder

- ID: `variational_lossy_autoencoder`
- Authors: Xi Chen, Diederik P. Kingma, Tim Salimans, Yan Duan, Prafulla Dhariwal, John Schulman, Ilya Sutskever, Pieter Abbeel
- Year: 2016
- Category: `representation_learning`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1611.02731, https://openai.com/index/variational-lossy-autoencoder/

### Core Idea

Constraining the decoder can make latent variables carry useful global information.

### Why It Mattered Historically

It addressed a key failure mode in generative latent-variable models with powerful decoders.

### Key Technical Concepts

- VAE
- latent variables
- posterior collapse
- lossy compression

### What A Beginner Should Understand

A summary should discard noise while preserving the information needed for the task.

### What Matters For Signal Engine 2.0

- Frames summarization and representation learning as controlled loss, not arbitrary compression
- Useful for future transcript abstraction experiments

### Possible Feature Ideas

- Lossy summary audit
- Latent topic sketch experiments
- Compression-vs-evidence preservation rubric

### Possible Evaluation Ideas

- Measure whether summaries preserve gold evidence spans
- Compare abstraction levels for reviewer usefulness

### Risks / Limitations

- Generative modeling is not implemented
- Lossy compression can hide legally/financially important nuance

## Relational Recurrent Neural Networks

- ID: `relational_recurrent_neural_networks`
- Authors: Adam Santoro, Ryan Faulkner, David Raposo, Jack Rae, Mike Chrzanowski, Theophane Weber, Daan Wierstra, Oriol Vinyals, Razvan Pascanu, Timothy Lillicrap
- Year: 2018
- Category: `reasoning_memory`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1806.01822

### Core Idea

Memory can be represented as interacting slots, making recurrent models better at relational reasoning.

### Why It Mattered Historically

It connected memory-augmented sequence models with relation-centric computation.

### Key Technical Concepts

- relational memory
- multi-slot memory
- self-attention over memory
- RNN

### What A Beginner Should Understand

A call has several active threads; one hidden state may be too cramped to track them all.

### What Matters For Signal Engine 2.0

- Good conceptual model for maintaining multiple transcript threads: guidance, risk, analyst pressure, and callbacks
- Bridges memory and relation reasoning

### Possible Feature Ideas

- Multi-thread call state tracker
- Topic memory slots
- Q&A callback detector

### Possible Evaluation Ideas

- Evaluate callback detection across sections
- Track topic-thread state against human annotations

### Risks / Limitations

- Research model not implemented
- Memory slots need labels or strong evaluation to be credible

## Quantifying the Rise and Fall of Complexity in Closed Systems: The Coffee Automaton

- ID: `coffee_automaton_complexity_closed_systems`
- Authors: Scott Aaronson, Sean M. Carroll, Lauren Ouellette
- Year: 2014
- Category: `compression_mdl_complexity`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1405.6903, https://www.scottaaronson.com/papers/coffee.pdf

### Core Idea

A simple automaton can model complexity rising and falling as two liquids mix toward equilibrium.

### Why It Mattered Historically

It operationalized the complexodynamics intuition in a concrete closed-system toy model.

### Key Technical Concepts

- cellular automata
- complexity dynamics
- coarse graining
- Kolmogorov complexity

### What A Beginner Should Understand

Complexity can be a time series; the most informative state may not be the beginning or end.

### What Matters For Signal Engine 2.0

- Suggests measuring information dynamics over an earnings call rather than treating all sections equally
- Useful for signal density timelines

### Possible Feature Ideas

- Signal density curve
- Prepared-to-Q&A complexity shift metric
- Boilerplate decay detector

### Possible Evaluation Ideas

- Compare signal density by call phase
- Test whether Q&A complexity predicts review priority

### Risks / Limitations

- Toy physical model, not transcript semantics
- Compression and complexity metrics require careful normalization

## Neural Turing Machines

- ID: `neural_turing_machines`
- Authors: Alex Graves, Greg Wayne, Ivo Danihelka
- Year: 2014
- Category: `reasoning_memory`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1410.5401

### Core Idea

A neural controller can learn to read and write from external memory using differentiable operations.

### Why It Mattered Historically

It was a landmark in memory-augmented neural networks and algorithmic task learning.

### Key Technical Concepts

- differentiable memory
- content addressing
- location addressing
- read/write heads

### What A Beginner Should Understand

Long reasoning often needs an external memory, not just a larger hidden state.

### What Matters For Signal Engine 2.0

- Inspires explicit memory/retrieval components for long transcripts instead of stuffing everything into one context
- Relevant to RAG and persistent evidence stores

### Possible Feature Ideas

- Evidence memory store
- Transcript scratchpad interface
- Memory-read audit log

### Possible Evaluation Ideas

- Evaluate retrieval memory hit rate
- Audit whether generated summaries cite stored evidence

### Risks / Limitations

- Original NTM is hard to train and not a practical repo component
- External memory needs transparent indexing and auditability

## Deep Speech 2: End-to-End Speech Recognition in English and Mandarin

- ID: `deep_speech_2_end_to_end_speech_recognition`
- Authors: Dario Amodei, Rishita Anubhai, Eric Battenberg, Carl Case, Jared Casper, Bryan Catanzaro, Jingdong Chen, Mike Chrzanowski, Adam Coates, Greg Diamos, Erich Elsen, Jesse Engel, Linxi Fan, Christopher Fougner, Tony Han, Awni Hannun, Billy Jun, Patrick LeGresley, Libby Lin, Sharan Narang, Andrew Ng, Sherjil Ozair, Ryan Prenger, Jonathan Raiman, Sanjeev Satheesh, David Seetapun, Shubho Sengupta, Yi Wang, Zhiqian Wang, Chong Wang, Bo Xiao, Dani Yogatama, Jun Zhan, Zhenyao Zhu
- Year: 2015
- Category: `speech_audio`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/1512.02595, https://proceedings.mlr.press/v48/amodei16.pdf

### Core Idea

A large end-to-end neural system can replace many hand-engineered speech recognition pipeline components.

### Why It Mattered Historically

It showed end-to-end ASR could work at scale across languages when paired with data and compute discipline.

### Key Technical Concepts

- end-to-end ASR
- CTC
- RNN acoustic models
- data scale
- HPC

### What A Beginner Should Understand

Speech intelligence starts with transcription quality, data scale, and measurable error rates.

### What Matters For Signal Engine 2.0

- Guides future audio transcript quality and prosody roadmap without requiring paid APIs
- Clarifies that ASR quality is a core dependency for audio-first signal claims

### Possible Feature Ideas

- ASR provenance manifest
- WER/proxy quality gate
- Prosody-aligned transcript feature roadmap

### Possible Evaluation Ideas

- Track ASR word error on any manually checked clips
- Compare transcript-only vs transcript+prosody on reviewed labels

### Risks / Limitations

- Training ASR is out of scope
- Audio claims require legally safe media and quality labels

## Scaling Laws for Neural Language Models

- ID: `scaling_laws_neural_language_models`
- Authors: Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B. Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, Dario Amodei
- Year: 2020
- Category: `scaling_systems`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/2001.08361

### Core Idea

Language model loss follows predictable power-law trends with model size, data size, and compute over broad ranges.

### Why It Mattered Historically

It helped turn model scaling into an empirical planning discipline.

### Key Technical Concepts

- scaling laws
- power laws
- dataset size
- compute
- model size
- cross-entropy loss

### What A Beginner Should Understand

More model is not automatically better; data, compute, and evaluation must scale together.

### What Matters For Signal Engine 2.0

- Supports a disciplined 30/100/500 transcript roadmap and stops premature large-model training
- Frames when more data matters more than model cleverness

### Possible Feature Ideas

- Transcript-count gates
- Learning curve dashboard
- Compute/data/model decision rubric

### Possible Evaluation Ideas

- Plot learning curves for local baselines by transcript count
- Pre-register evaluation gates before scaling

### Risks / Limitations

- Original results concern large LMs, not tiny finance classifiers
- Later scaling-law work changed some optimal-data conclusions

## A Tutorial Introduction to the Minimum Description Length Principle

- ID: `tutorial_minimum_description_length_principle`
- Authors: Peter D. Grunwald
- Year: 2004
- Category: `evaluation_theory`
- Implementation status: `research_only`
- Confidence: `high`
- Sources: https://arxiv.org/abs/math/0406077

### Core Idea

The best model can be viewed as the one that compresses data well, balancing model description and residual errors.

### Why It Mattered Historically

It is a foundational tutorial for information-theoretic model selection.

### Key Technical Concepts

- MDL
- model selection
- two-part codes
- compression
- generalization

### What A Beginner Should Understand

A good explanation should make the data shorter without hiding mistakes.

### What Matters For Signal Engine 2.0

- Provides evaluation philosophy for choosing simple explainable models until evidence justifies complexity
- Useful for weak-label and active-learning governance

### Possible Feature Ideas

- Model selection notes
- Weak-label complexity penalty
- Evidence-quality vs model-complexity dashboard

### Possible Evaluation Ideas

- Track errors saved per added feature
- Compare deterministic rules vs learned models under a simplicity rubric

### Risks / Limitations

- The principle is conceptual unless converted into concrete metrics
- MDL can be mathematically heavy for portfolio readers

## Machine Super Intelligence

- ID: `machine_super_intelligence`
- Authors: Shane Legg
- Year: 2008
- Category: `evaluation_theory`
- Implementation status: `research_only`
- Confidence: `medium`
- Sources: https://www.vetta.org/documents/Machine_Super_Intelligence.pdf, https://www.inf.usi.ch/en/feeds/8625

### Core Idea

A theoretical study of universal artificial intelligence and superintelligent agents.

### Why It Mattered Historically

It influenced later AGI and DeepMind-era thinking about intelligence, capability, and safety.

### Key Technical Concepts

- universal intelligence
- AIXI
- agent evaluation
- superintelligence
- theoretical AI

### What A Beginner Should Understand

Big intelligence claims require formal definitions and careful limits.

### What Matters For Signal Engine 2.0

- Useful mainly as a caution against overclaiming intelligence in Signal Engine 2.0
- Encourages precise task definitions and bounded claims

### Possible Feature Ideas

- Capability-claim checklist
- AI tool risk register
- Evaluation boundary statement

### Possible Evaluation Ideas

- Audit product language for unsupported AI claims
- Separate tool assistance from validated reasoning ability

### Risks / Limitations

- Not an applied earnings-call paper
- Theoretical framing can distract from concrete evaluation

## Kolmogorov Complexity and Algorithmic Randomness

- ID: `kolmogorov_complexity_algorithmic_randomness`
- Authors: Alexander Shen, Vladimir A. Uspensky, Nikolay Vereshchagin
- Year: 2017
- Category: `compression_mdl_complexity`
- Implementation status: `research_only`
- Confidence: `medium`
- Sources: https://www.ams.org/bookpages/surv-220

### Core Idea

Algorithmic information theory studies the shortest descriptions of objects and formal notions of randomness.

### Why It Mattered Historically

It provides the mathematical background behind MDL, complexity, and randomness discussions on the list.

### Key Technical Concepts

- Kolmogorov complexity
- algorithmic randomness
- Martin-Lof randomness
- description length

### What A Beginner Should Understand

Random-looking text can be hard to compress but still useless; complexity needs task context.

### What Matters For Signal Engine 2.0

- Deep foundation for compression-based novelty, boilerplate, and signal-density ideas
- Supports honest uncertainty around what compression metrics can and cannot prove

### Possible Feature Ideas

- Boilerplate/compressibility research note
- Randomness-vs-signal caveat in feature docs

### Possible Evaluation Ideas

- Validate compression metrics against human labels
- Check false positives on boilerplate and legal disclaimers

### Risks / Limitations

- Book-level theory, not an implementation
- Kolmogorov complexity is uncomputable in general

## Stanford's CS231n Convolutional Neural Networks for Visual Recognition

- ID: `stanford_cs231n_convolutional_neural_networks`
- Authors: Fei-Fei Li, Andrej Karpathy, Justin Johnson
- Year: 2015
- Category: `vision_multimodal`
- Implementation status: `research_only`
- Confidence: `medium`
- Sources: https://cs231n.stanford.edu/, https://cs231n.github.io/

### Core Idea

A practical course resource for understanding and training convolutional neural networks for visual recognition.

### Why It Mattered Historically

CS231n educated a generation of deep learning practitioners and tied theory to implementation practice.

### Key Technical Concepts

- CNN fundamentals
- optimization
- backpropagation
- computer vision
- practical training

### What A Beginner Should Understand

Before using visual features, understand data, architecture, optimization, and error analysis.

### What Matters For Signal Engine 2.0

- Training-ground reference for future multimodal feature extraction and model-card literacy
- Useful to keep visual/audio claims grounded in fundamentals

### Possible Feature Ideas

- Multimodal learning syllabus
- Vision feature audit checklist
- Model-card review guide

### Possible Evaluation Ideas

- Require visual feature coverage reports
- Compare multimodal lift with human-reviewed decision tasks

### Risks / Limitations

- Course resource, not a single paper
- Visual recognition is only indirectly relevant to transcript-first earnings calls
