# Public Resource Fit Report

This report ranks public resources for Signal Engine 2.0 using conservative fit and risk scores.
It is a planning aid, not a claim that these resources should become canonical or default dependencies.

## Ranking Table

| rank | resource | fit | why-not | phase | path | access |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Loughran-McDonald Master Dictionary | 9 | 3 | now | canonical | available |
| 2 | Financial PhraseBank | 7 | 5 | next | benchmark_only | needs_verification |
| 3 | Switchboard Dialog Act Corpus / MRDA | 6 | 6 | next | benchmark_only | gated |
| 4 | FinBERT | 6 | 7 | later | benchmark_only | available |
| 5 | openSMILE | 5 | 7 | later | optional_adapter | available |
| 6 | MELD | 4 | 8 | later | benchmark_only | available |
| 7 | OpenCV | 4 | 8 | later | optional_adapter | available |
| 8 | CMU-MOSEI | 3 | 9 | avoid_for_now | documentation_only | needs_verification |

## Detailed Notes

### Loughran-McDonald Master Dictionary

- primary_url: [https://sraf.nd.edu/loughranmcdonald-master-dictionary/](https://sraf.nd.edu/loughranmcdonald-master-dictionary/)
- resource_type / modality: `dictionary` / `transcript`
- fit / why-not: `9` / `3`
- recommended_phase: `now`
- default_path: `canonical`
- implementation_effort: `low`
- risk_level: `low`
- access: available
- license_or_access_notes: Official Notre Dame academic distribution is public; review terms before vendoring dictionary files.
- best_use_in_signal_engine: Extend canonical deterministic finance lexicons and benchmark transcript-only feature coverage.
- why_fit: Best fit for deterministic finance-language extension, especially uncertainty, modal strength, and constraint cues that can stay auditable.
- why_not: Dictionary counts still need conversational context and do not solve dialogue structure or multi-domain review on their own.
- notes: Strongest immediate fit for earnings-call terminology without adding model dependencies.

### Financial PhraseBank

- primary_url: [https://arxiv.org/abs/1307.5336](https://arxiv.org/abs/1307.5336)
- resource_type / modality: `dataset` / `transcript`
- fit / why-not: `7` / `5`
- recommended_phase: `next`
- default_path: `benchmark_only`
- implementation_effort: `medium`
- risk_level: `medium`
- access: needs_verification
- license_or_access_notes: Original paper is public; mirrors often expose separate dataset terms, so reuse should be re-checked before local benchmarking.
- best_use_in_signal_engine: Benchmark-only transcript sanity checks for finance sentiment, not canonical scoring.
- why_fit: Useful small finance benchmark for sanity-checking sentiment behavior on short financial text.
- why_not: Short headline sentiment does not map cleanly to transcript evidence, analyst pressure, or reviewer actionability.
- notes: Helpful evaluation reference, but weaker fit than transcript-specific lexicon work.

### Switchboard Dialog Act Corpus / MRDA

- primary_url: [https://catalog.ldc.upenn.edu/LDC97S62](https://catalog.ldc.upenn.edu/LDC97S62)
- resource_type / modality: `corpus` / `transcript_audio`
- fit / why-not: `6` / `6`
- recommended_phase: `next`
- default_path: `benchmark_only`
- implementation_effort: `medium`
- risk_level: `medium`
- access: gated
- license_or_access_notes: Core corpora are gated through LDC or research distribution; metadata and papers are accessible.
- best_use_in_signal_engine: Dialogue-act taxonomy reference and later benchmark-only experiments if access becomes available.
- why_fit: Strong conceptual fit for question-answer structure, interruptions, and conversational move taxonomies.
- why_not: Access is gated and the domains are not earnings, support, or sales, so direct adoption would add friction.
- notes: Good methodology reference, but not a default-path dependency.

### FinBERT

- primary_url: [https://huggingface.co/ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert)
- resource_type / modality: `model` / `transcript`
- fit / why-not: `6` / `7`
- recommended_phase: `later`
- default_path: `benchmark_only`
- implementation_effort: `medium`
- risk_level: `medium`
- access: available
- license_or_access_notes: Model card is public; downstream commercial and data-provenance review is still advisable before broader use.
- best_use_in_signal_engine: Optional benchmark-only comparator for finance text, especially earnings-call phrasing.
- why_fit: Good optional finance-domain comparison point for transcript sentiment benchmarking.
- why_not: Black-box sentiment scores are too narrow and too opaque to become canonical signal extraction in this repo.
- notes: Useful as a measured comparator, not as product truth.

### openSMILE

- primary_url: [https://www.audeering.com/research/opensmile/](https://www.audeering.com/research/opensmile/)
- resource_type / modality: `tool` / `audio`
- fit / why-not: `5` / `7`
- recommended_phase: `later`
- default_path: `optional_adapter`
- implementation_effort: `medium`
- risk_level: `medium`
- access: available
- license_or_access_notes: audEERING documents research-oriented usage; commercial usage requires care.
- best_use_in_signal_engine: Optional audio adapter for sparse prosody cues in later pilot cases.
- why_fit: Strong bounded fit for pauses, energy, and prosodic review cues without claiming hidden-state inference.
- why_not: Audio features add dependency and rights complexity and should not be interpreted as internal-state truth.
- notes: Only useful once aligned approved audio exists.

### MELD

- primary_url: [https://affective-meld.github.io/](https://affective-meld.github.io/)
- resource_type / modality: `dataset` / `multimodal`
- fit / why-not: `4` / `8`
- recommended_phase: `later`
- default_path: `benchmark_only`
- implementation_effort: `high`
- risk_level: `high`
- access: available
- license_or_access_notes: Public project resources exist, but media provenance and downstream reuse posture should be treated carefully.
- best_use_in_signal_engine: Benchmark framing only for future multimodal comparisons, not core pipeline work.
- why_fit: Useful research reference for multimodal conversation emotion benchmarks and evaluation language.
- why_not: Friends-based emotion labels are a weak fit for enterprise transcript review and recruiter-facing proof.
- notes: Keep this in documentation until aligned business-conversation media exists.

### OpenCV

- primary_url: [https://opencv.org/](https://opencv.org/)
- resource_type / modality: `library` / `video`
- fit / why-not: `4` / `8`
- recommended_phase: `later`
- default_path: `optional_adapter`
- implementation_effort: `low`
- risk_level: `medium`
- access: available
- license_or_access_notes: OpenCV 4.5.0+ is Apache 2.0; older versions are BSD-licensed.
- best_use_in_signal_engine: Optional video utility layer for later sparse cue extraction only.
- why_fit: Lightweight fit for frame stats, motion proxies, and simple video preprocessing if sparse visual review is added later.
- why_not: Basic vision utilities do not justify body-language certainty claims and are far from canonical transcript evaluation.
- notes: Best treated as infrastructure, not as inference evidence on its own.

### CMU-MOSEI

- primary_url: [https://github.com/CMU-MultiComp-Lab/CMU-MultimodalSDK](https://github.com/CMU-MultiComp-Lab/CMU-MultimodalSDK)
- resource_type / modality: `dataset` / `multimodal`
- fit / why-not: `3` / `9`
- recommended_phase: `avoid_for_now`
- default_path: `documentation_only`
- implementation_effort: `high`
- risk_level: `high`
- access: needs_verification
- license_or_access_notes: Widely cited research benchmark, but current practical access/download path should be re-verified before use.
- best_use_in_signal_engine: Documentation-only cautionary reference for later multimodal benchmarking decisions.
- why_fit: Only useful as a broad multimodal sentiment benchmark reference.
- why_not: Generic multimodal sentiment/emotion is a poor fit for transcript-first, evidence-backed business signal extraction.
- notes: Low portfolio fit for the current repo direction.

## What Not To Do

- Do not make FinBERT, MELD, or CMU-MOSEI canonical for this repo on the basis of this report alone.
- Do not turn openSMILE or OpenCV features into truth claims about hidden emotion, deception, or intent.
- Do not assume public mirrors are commercially clean without re-checking dataset or model terms.
- Do not make gated corpora like Switchboard or MRDA part of default CI or setup requirements.
