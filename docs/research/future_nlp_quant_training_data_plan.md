# Future NLP / Quant Training Data Plan

## 1. Goal

The goal is to collect rights-safe, evidence-backed, reviewable data that can later support deterministic rule improvement, weak-label evaluation, supervised NLP classification, retrieval evaluation, long-context review benchmarking, event-study packaging, and retail baseline comparison.

This plan is training-readiness oriented. It does not create training data from proprietary sources, copy raw transcript text, or claim a trading edge.

## 2. What data is needed

Signal Engine needs structured metadata and review artifacts before it needs larger models:

- transcript metadata
- call metadata
- company metadata
- fiscal period metadata
- transcript section metadata
- speaker-role metadata
- Q&A pair metadata
- guidance statement objects
- guidance revision objects
- uncertainty / hedging objects
- analyst-pressure objects
- reassurance objects
- answer-shift objects
- evidence spans
- reviewer decisions
- false-positive tags
- retrieval objects
- later market reaction metadata

The unit of value is not a raw transcript. The unit of value is a rights-safe, provenance-preserving case with candidate signals, evidence locations, reviewer decisions, and evaluation status.

## 3. Rights-safe acquisition rules

- Register source path and hash rather than raw proprietary text.
- Prefer company IR, SEC, and explicitly allowed sources where possible.
- Use licensed vendor material only if the license permits the intended storage, review, and training use.
- Do not bypass paywalls.
- Do not bypass logins.
- Do not bypass robots.txt or source terms.
- Do not redistribute restricted text.
- Do not commit raw transcript text unless rights and repo policy allow it.
- Do not train models on restricted text unless rights are clear.
- Keep local-only evidence text local when rights are uncertain.
- Store repo-safe spans, hashes, metadata, and source pointers where raw text cannot be committed.

## 4. Minimum viable training dataset

The minimum viable dataset is a 30-call pilot with the first 100 valid human-reviewed labels. It should be balanced across:

- guidance_revision
- analyst_pressure
- management_hedging
- uncertainty
- reassurance
- answer_shift
- neutral/no_signal

The pilot should prioritize clear review cases before difficult edge cases. Ambiguous examples are useful, but they should be tagged as calibration material rather than treated as proof of model quality.

## 5. Expanded dataset roadmap

The next step after the pilot is a 100-150 call corpus with stronger balance and richer metadata:

- sector balance
- mega-cap / mid-cap balance
- obvious revision / no-revision balance
- clean / messy transcript balance
- transcript-only / audio-backed / video-backed availability flags
- prepared-remarks / Q&A balance
- analyst-heavy / analyst-light call balance
- rights-cleared and local-only separation

The 500-call metadata universe should remain metadata-first until source rights, storage policy, and review capacity are ready. It can support target selection, stratification, source-quality tracking, and future evaluation design without importing raw text.

## 6. Feature families

Future features should stay close to reviewable transcript structure:

- lexical
- section-aware
- speaker-role-aware
- Q&A structure
- revision-direction
- uncertainty/hedging
- reassurance
- analyst pressure
- answer evasiveness
- evidence quality
- retrieval features
- event-study features
- audio later
- video later

Audio and video should remain optional audit layers. They should add metadata for flagged moments, not replace transcript-first evidence.

## 7. Label schema direction

A future label object should support:

- label_id
- case_id
- ticker
- company
- fiscal_period
- signal_type
- expected_direction
- transcript_section
- speaker_role
- topic
- evidence_start_hint
- evidence_end_hint
- evidence_text_hash or excerpt policy
- confidence
- reviewer
- reviewed_at
- false_positive_tag
- notes

The schema should not require raw evidence text when rights are unclear. It should allow local-only evidence text, repo-safe hashes, and span hints. If excerpts are permitted, the excerpt policy should record why the text can be stored and reused.

## 8. Training-readiness gates

Training or model benchmarking should not begin until these gates pass:

- minimum label count
- minimum per-label support
- reviewer agreement check
- false-positive audit complete
- no-leakage check
- source rights check
- schema validation pass
- baseline comparison available
- fixture and demo cases separated from evaluation claims
- candidate labels clearly separated from gold labels

The default answer before these gates pass should be "not training-ready yet."

## 9. Future model tracks

The safe model roadmap is staged:

- deterministic rules for canonical extraction
- weak-label filtering for reviewer prioritization
- supervised classifier after adequate human labels
- retrieval/reranking after evidence objects exist
- long-context reviewer benchmark on bounded case bundles
- event-study packaging as exploratory metadata analysis
- selective multimodal audit for flagged moments only

Each track should report status as planned, scaffolded, gated, or built. No model track should override deterministic extraction without explicit review and evaluation.

## 10. Non-goals

- No live trading.
- No alpha claims.
- No automated execution.
- No buy/sell/hold recommendations.
- No unsupported statistical significance claims.
- No restricted-source training.
- No raw transcript copying from proprietary sources.
- No weak-label promotion without human adjudication.
