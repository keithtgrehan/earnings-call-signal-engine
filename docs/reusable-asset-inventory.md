# Reusable Asset Inventory

Source report: `/Users/keith/Desktop/repo_sync_signal_engine_2_0_report.md`

This inventory converts the local repo-sync report into a practical reuse queue for Signal Engine 2.0. It is intentionally docs-only: no safety branches were merged, no implementation code was imported, and no generated artifacts were touched.

## Immediate Reuse Candidates

- Portfolio proof tooling: import the concepts from `scripts/build_portfolio_proof.py` later as a lightweight proof/report pattern for Signal Engine 2.0 demo outputs, not as a direct branch merge.
- Markdown link checker: consider importing or adapting `scripts/check_markdown_links.py` now because it is small, deterministic, and useful for keeping buyer/demo docs credible.
- Proof freshness checker: consider adapting `scripts/check_proof_freshness.py` now for demo freshness checks that verify output artifacts still match the documented proof path.
- Case-study and demo doc patterns: reuse the structure from `docs/case-study.md`, `docs/demo-path.md`, and `docs/freeze-boundaries.md` as content patterns for buyer-facing Signal Engine 2.0 walkthroughs.
- Clarity schema and safety ideas: keep as later-only references for consent, privacy, matching, moderation, and explainability language. Do not import Clarity application code into Signal Engine 2.0 now.

## Reuse Decision Table

| Asset category | Source repo/path | Reuse candidate | Recommended action | Rationale | Risk |
| --- | --- | --- | --- | --- | --- |
| Deterministic parser | `earnings-call-signal-engine` active workspace: `src/signal_engine/pipeline.py` | Current Signal Engine 2.0 normalization and analysis path | Import now | Already canonical in this branch and aligned with transcript-first scoring | Low; keep behavior covered by existing tests |
| Conversation schema | `earnings-call-signal-engine` active workspace: `src/signal_engine/schemas.py`, `docs/domain-schemas.md` | Unified conversation and evidence schema | Import now | Already supports support, sales, account management, and earnings-call domains | Low; avoid widening schema without tests |
| Feature extraction | `earnings-call-signal-engine` active workspace: `src/signal_engine/text_features.py`, `src/signal_engine/role_features.py` | Deterministic text and role/turn features | Import now | Directly supports Signal Engine 2.0 and remains offline | Low; watch false positives in lexicons |
| Risk flag logic | `earnings-call-signal-engine` active workspace: `src/signal_engine/risk_rules.py` | Domain-specific risk and opportunity flags | Import now | Core product behavior already lives here | Medium; rule changes alter user-facing scores |
| Demo data | `earnings-call-signal-engine` active workspace: `data/signal_engine_2_0/*.json` | Tiny support, sales, and account-management samples | Import now | Small, readable, and useful for repeatable demos | Low; keep samples synthetic and tiny |
| Demo report and copy | `earnings-call-signal-engine` active workspace: `demo/signal_engine_2_0/demo_report.md`, `buyer_one_pager.md` | Buyer-facing narrative and pilot copy | Import now | Helps explain deterministic outputs to nontechnical reviewers | Low; keep claims tied to evidence |
| Library and multimodal roadmap | `earnings-call-signal-engine` active workspace: `docs/library-evaluation-matrix.md`, `docs/multimodal-stack.md` | Optional dependency and future-readiness framing | Import now | Keeps built-now scope separate from roadmap | Low; avoid making heavy tools required |
| Legacy support-QA parser baseline | Clean feature clone: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026/src/parser.py` | Prior simple conversation parser | Later | Useful reference for fallback parsing, but current schema is broader | Medium; clone branch is behind remote |
| Legacy support-QA features | Clean feature clone: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026/src/features.py` | Simple directness, deflection, and consistency features | Later | Useful comparison baseline for deterministic scoring | Medium; duplicate behavior could diverge |
| Legacy support-QA tests | Clean feature clone: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026/tests/test_features.py` | Regression patterns for deterministic scoring | Later | Good examples for edge cases and repeatability checks | Low; adapt tests rather than importing wholesale |
| Portfolio proof builder | Safety branch `safety/sync-20260424-130930`: `scripts/build_portfolio_proof.py` | Proof artifact summarizer for demo outputs | Import now | Small enough to adapt and useful for buyer/demo credibility | Medium; original target assumes legacy earnings outputs |
| Markdown link checker | Safety branch `safety/sync-20260424-130930`: `scripts/check_markdown_links.py` | Local markdown/path sanity checker | Import now | Deterministic and valuable for docs-heavy demo work | Low; current repo already has a version |
| Proof freshness checker | Safety branch `safety/sync-20260424-130930`: `scripts/check_proof_freshness.py` | Output freshness guard | Import now | Can protect demo JSON and proof docs from drifting | Medium; needs retargeting away from legacy artifacts |
| README proof refresher | Safety branch `safety/sync-20260424-130930`: `scripts/refresh_readme_proof.py` | Automated README proof block updater | Later | Useful once Signal Engine 2.0 proof metrics stabilize | Medium; could churn README if adopted too early |
| Portfolio docs audit | Safety branch `safety/sync-20260424-130930`: `scripts/audit_portfolio_docs.py` | Consistency checker for portfolio-facing docs | Later | Helpful after demo docs settle | Medium; legacy assumptions may not match Signal Engine 2.0 |
| Case-study doc pattern | Safety branch `safety/sync-20260424-130930`: `docs/case-study.md` | Narrative case-study structure | Import now | Directly reusable for buyer-facing walkthroughs | Low; use as structure, not canonical facts |
| Demo path doc pattern | Safety branch `safety/sync-20260424-130930`: `docs/demo-path.md` | Demo runbook pattern | Import now | Useful for repeatable demo instructions | Low; update commands to current sample paths |
| Freeze boundary doc pattern | Safety branch `safety/sync-20260424-130930`: `docs/freeze-boundaries.md` | Built-now versus later boundary language | Import now | Matches Signal Engine 2.0 scope discipline | Low |
| Retrieval boundary doc pattern | Safety branch `safety/sync-20260424-130930`: `docs/retrieval-boundary.md` | Boundary between deterministic truth and retrieval assistance | Later | Useful once retrieval experiments return | Medium; avoid implying retrieval is canonical |
| Local review server | Safety branch `safety/sync-20260424-130930`: `app/site_server.py` | Lightweight local artifact browser pattern | Later | Could help demos eventually, but UI is out of current scope | Medium; user explicitly said no UI for this pass |
| CI workflow pattern | Safety branch `safety/sync-20260424-130930`: `.github/workflows/portfolio-ci.yml` | CI shape for docs/proof checks | Later | Useful once Signal Engine 2.0 checks are stable | Medium; legacy proof paths can fail if copied directly |
| Audio transcript processing | Earnings-call preservation clone: `src/earnings_call_sentiment/transcriber.py` | Optional ASR/transcript adapter reference | Later | Relevant to future multimodal roadmap | High; heavy dependencies and external media assumptions |
| Audio feature modules | Earnings-call preservation clone: `src/earnings_call_sentiment/audio/` | Optional pause/prosody feature references | Later | Useful when adding audio enrichment after text-first baseline | High; do not make audio dependencies required |
| Video feature modules | Earnings-call preservation clone: `src/earnings_call_sentiment/visual/` | Optional keyframe and visual behavior references | Later | Good reference for future flagged-moment review | High; generated artifacts and media dependencies are heavy |
| WhisperX alignment script | Earnings-call preservation clone: `scripts/run_whisperx_alignment.py` | Optional transcript alignment reference | Later | Relevant only after ASR/diarization scope is approved | High; model/runtime requirements |
| OpenFace script | Earnings-call preservation clone: `scripts/run_openface_features.py` | Optional visual feature extraction reference | Later | Future multimodal review only | High; external runtime and generated artifacts |
| Clarity shared schemas | `clarity-ai-transparent-dating` main clone: `packages/shared/src/schemas/domain.ts`, `contracts.ts` | Schema design ideas for profiles, consent, and contracts | Later | Useful as a typed schema reference for Clarity/Vibe reuse | Medium; product domain differs from conversation intelligence |
| Clarity matching service | `clarity-ai-transparent-dating` main clone: `apps/api/src/services/matching.ts` | Explainable matching/ranking ideas | Later | Conceptually useful for deterministic compatibility scoring | High; app-specific implementation should not be imported |
| Clarity moderation service | `clarity-ai-transparent-dating` main clone: `apps/api/src/services/moderation.ts` | Safety and review workflow ideas | Later | Good reference for privacy/safety thinking | High; domain and compliance context differ |
| Clarity AI boundary docs | `clarity-ai-transparent-dating` main clone: `AI_BOUNDARIES.md`, `SAFETY_PRINCIPLES.md`, `docs/safety/*.md` | Product copy and safety framing | Later | Useful language for explainability and user trust | Medium; adapt carefully to enterprise conversation review |
| Clarity product copy | `clarity-ai-transparent-dating` main clone: `PRODUCT_BRIEF.md`, `USER_PERSONAS.md`, `docs/growth/OUTREACH_TEMPLATES.md` | Buyer/persona copy references | Later | Useful for packaging Clarity and VibeSignal later | Low; not directly Signal Engine 2.0 behavior |
| Clarity matching prototype | Desktop preserve branch `sync/local-preserve-20260424-130930`: `clarity_matching_engine.py` | Deterministic scoring prototype for matching | Later | Useful conceptual parallel for explainable scoring | Medium; separate domain and quality uncertain |
| Clarity sample profiles | Desktop preserve branch `sync/local-preserve-20260424-130930`: `clarity_sample_profiles.json`, `clarity_sample_match_output.json` | Small demo data/output pattern | Later | Good example of pairing sample input with explainable output | Medium; keep out of Signal Engine canonical samples |
| Clarity matching architecture docs | Desktop preserve branch `sync/local-preserve-20260424-130930`: `clarity_matching_architecture.md`, `matching_engine_plan*.md` | Architecture and roadmap references | Later | Useful for future Clarity/VibeSignal planning | Low |
| VibeSignal assets | `vibe-signal` local clone | Any VibeSignal-specific reusable patterns | Reject | No local clone was found in the searched paths | High; cannot evaluate or import missing assets |

## Do Not Import Yet

- Generated multimodal artifacts, including `data/processed/multimodal/visual/.../clips/` and `data/processed/multimodal/visual/.../openface_raw/`.
- PDFs, DOCX files, screenshots, image leftovers, zip files, `.DS_Store`, `__pycache__`, and other loose desktop artifacts from the Clarity preserve clone.
- Clarity app implementation code from `apps/api/`, `apps/web/`, or `packages/shared/` as direct Signal Engine 2.0 imports.
- Any VibeSignal/VibeCheck assets until a local clone is found and inspected.
- Heavy ASR, diarization, audio, or video processing modules until the text-first Signal Engine 2.0 path has a dedicated multimodal integration plan.
- Safety-branch CI workflows or proof scripts copied verbatim, because several still assume legacy earnings-call artifact paths.

## Recommended Next Actions

- Adapt the markdown link checker and proof freshness idea only if they can point at current Signal Engine 2.0 docs and demo artifacts.
- Use the portfolio and case-study docs as structure for buyer-facing narratives, not as a source of canonical product claims.
- Keep Clarity schemas, safety docs, and matching prototype as reference material for later Clarity/VibeSignal reuse.
- Treat multimodal code as roadmap reference until a small, optional, transcript-preserving adapter is explicitly scoped.
