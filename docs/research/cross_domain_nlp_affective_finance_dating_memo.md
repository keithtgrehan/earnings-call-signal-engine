# Cross-Domain NLP Affective Finance Dating Memo

Status: research memo only. This does not add data ingestion, raw dating data, model training, provider outputs, production classifiers, emotion recognition, trading logic, or relationship-scoring logic.

Core statement: observable cues only, no true emotion/deception claims.

## Finance NLP research summary

Finance NLP is useful for grounding Signal Engine in benchmarkable tasks: document QA, numeric reasoning, evidence retrieval, financial phrase classification, earnings-call summarization, and finance-specific tone. The relevant resources are benchmark and research references, not automatic production dependencies.

Resource radar:

- FinBERT: finance-language transformer baseline for text classification research.
- FinGPT: finance LLM research ecosystem; useful as a comparison target, not a source of canonical truth.
- FinanceBench: financial QA benchmark for retrieval and faithfulness evaluation.
- FinMTEB: finance embedding benchmark suite for retrieval comparisons.
- FinBen: broad finance benchmark suite for language-model evaluation.
- FLaME: financial language model evaluation reference.
- Open FinLLM Leaderboard: model comparison reference, not a production approval list.
- ECTSum: earnings-call summarization benchmark reference.
- Financial PhraseBank: financial sentiment phrase dataset, benchmark-only unless rights review says otherwise.
- FiQA: financial QA/sentiment reference.
- FinQA: financial numerical reasoning benchmark.
- ConvFinQA: conversational financial reasoning benchmark.
- Loughran-McDonald: finance lexicon reference for deterministic lexical financial tone.

Signal Engine should continue to treat deterministic transcript extraction as canonical. Finance NLP resources can help define benchmark tasks and failure analysis, but they cannot create gold labels, trading claims, or alpha claims.

## Dating-app and relationship NLP safe-use summary

Dating-app or relationship NLP has a higher personal-safety and manipulation risk profile than finance document analysis. Safe uses require user ownership, opt-in consent, privacy minimization, and non-manipulative assistance.

Potential safe uses:

- opt-in message clarity feedback
- consent/safety classifier
- harassment/toxicity detection
- pressure-language detection
- user-owned message review
- conversation health summary for the user only
- non-manipulative response drafting
- local/private processing where possible

These features should help a user understand or improve their own communication. They must not score another person's inner state, attraction, vulnerability, attachment style, honesty, or susceptibility.

## Affective cue system summary

Affective cue systems can support review only when constrained to observable cue metadata. A pause, overlap, hedge, pressure phrase, or gaze-direction estimate is not a true emotion label. For Signal Engine, transcript features remain canonical; audio/video metadata, if ever used, must be reviewer-support only and rights-cleared.

Cross-domain implication: finance, dating, and affective systems all need the same safety pattern:

- rights/consent gate
- PII minimization
- deterministic baseline
- evidence objects
- reviewer-support output
- explicit red-line filters
- evaluation gates for unsupported claims

## Red lines

Dating-app red lines:

- "this person loves you"
- "this person is lying"
- emotional vulnerability scoring
- attraction prediction
- attachment-style inference without consent
- relationship manipulation suggestions
- sensitive trait inference

Affective cue red lines:

- no true emotion inference
- no universal emotion truth
- no deception detection
- no mental-health diagnosis
- no biometric identity inference
- no workplace/education emotion inference

Finance red lines:

- trading signal claims
- alpha claims
- buy/sell recommendations
- unsupported statistical significance
- machine labels treated as gold labels
- causal market claims without reviewed evidence and sufficient design

## Signal Engine implementation implications

- Keep transcript-first deterministic extraction as canonical.
- Use finance NLP resources for benchmark design, not gold-label promotion.
- Keep retrieval and BYOK reviewer layers bounded to fixed evidence bundles.
- Require provenance on every evidence object.
- Treat multimodal metadata as optional, flagged-window, rights-cleared, reviewer-support only context.
- Block trading, alpha, buy/sell, causal, deception, mental-health, biometric identity, and universal emotion truth claims.
- Keep human-adjudicated gold labels as the only evaluation truth source.

## Dating-app implementation implications

- Require opt-in consent and user-owned message scope.
- Prefer local/private processing where possible.
- Minimize PII and provide deletion/export controls.
- Provide clarity, safety, harassment, toxicity, and pressure-language feedback without manipulation.
- Avoid attraction prediction, emotional vulnerability scoring, relationship manipulation suggestions, sensitive trait inference, or claims that another person loves the user or is lying.
- Present outputs as candidate/reviewer-support only when human review or user judgment is required.

## Shared evaluation implications

- Measure precision, recall, macro F1, calibration, abstain rate, unsupported claim rate, citation quality, privacy redaction, and reviewer usefulness.
- Run red-line tests before benchmark claims.
- Keep external datasets benchmark-only by default.
- Document license, consent, allowed use, and source-rights status before expanding any registry.
