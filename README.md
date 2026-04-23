# Earnings Call Signal Engine
Transcript-first local review workflow for turning one earnings call into deterministic, auditable artifacts for analyst review.

This repo is a decision-support tool, not a trading system. It does not execute orders, does not claim predictive edge, and does not treat optional model or multimodal layers as the source of truth.

## What It Is
- A local workflow for ingesting one earnings call from transcript text, YouTube/media, or document text.
- A deterministic extraction layer that writes structured review artifacts such as `guidance.csv`, `metrics.json`, and `report.md`.
- A local review shell for inspecting source excerpts, extracted signals, ambiguity notes, and supporting context.
- An additive sidecar layer for audio, NLP, and video support when available, kept explicitly secondary to transcript-backed outputs.

## Why It Exists
Earnings calls are long, noisy, and easy to skim poorly. Reviewers need a fast way to answer:
- what changed
- where the supporting evidence lives
- which moments deserve attention first
- what is deterministic versus what is only supportive context

This repo packages that workflow into inspectable artifacts instead of relying on a black-box summary.

## Canonical Portfolio Proof
The public proof path for this repo is the checked-in Eli Lilly case bundle:
- output directory: `outputs/LLY_2025_Q2_call08/`
- quick verification:

```bash
python scripts/verify_outputs.py --out-dir outputs/LLY_2025_Q2_call08 --require-run-meta
```

- full portfolio check:

```bash
make portfolio-ci
```

Open these files in order:
- [`outputs/LLY_2025_Q2_call08/report.md`](outputs/LLY_2025_Q2_call08/report.md)
- [`outputs/LLY_2025_Q2_call08/metrics.json`](outputs/LLY_2025_Q2_call08/metrics.json)
- [`outputs/LLY_2025_Q2_call08/guidance.csv`](outputs/LLY_2025_Q2_call08/guidance.csv)
- [`docs/demo-path.md`](docs/demo-path.md)
- [`docs/portfolio-proof.md`](docs/portfolio-proof.md)

Fixed UI demo cases for Netflix, Meta, and NVIDIA still exist in the repo, but the Lilly bundle is the single recruiter-facing proof path because it is frozen, inspectable, and tied to a committed benchmark row. The benchmark note itself also records that the ASR text is imperfect, which is exactly the kind of limitation this repo is meant to surface instead of hiding.

## Proof (current state)
<!-- proof:begin -->
- Frozen benchmark label: `raised` for Eli Lilly (`call08`, 2025-08-07, confidence 0.78).
- Proof check runtime: 0.386975 seconds for `verify_outputs.py` against the committed bundle.
- Recorded run cost: not yet measured.
- Extracted signals in the committed bundle: 93 guidance rows, 19 uncertainty rows, 4 reassurance rows, 1 analyst-skepticism row(s).
- Example outputs: reviewer report at `outputs/LLY_2025_Q2_call08/report.md`.
- Example outputs: structured scorecard at `outputs/LLY_2025_Q2_call08/metrics.json`.
- Example outputs: extracted guidance table at `outputs/LLY_2025_Q2_call08/guidance.csv`.
<!-- proof:end -->

## What Goes In
- transcript text
- YouTube or local media
- local document text

## What Comes Out
- transcript artifacts: `transcript.json`, `transcript.txt`
- deterministic scoring artifacts: `chunks_scored.jsonl`, `guidance.csv`, `guidance_revision.csv`, `tone_changes.csv`
- signal tables: `uncertainty_signals.csv`, `reassurance_signals.csv`, `analyst_skepticism.csv`
- reviewer outputs: `metrics.json`, `report.md`, `run_meta.json`
- optional supporting artifacts: `qa_shift_summary.json`, `audio_behavior_summary.json`, `multimodal_support_summary.json`

The scorecard in `metrics.json` is a deterministic presentation layer over extracted evidence. It is meant to route reviewer attention into concrete categories, not replace the underlying files.

## Pilot Corpus And Retrieval
As of April 23, 2026, the repo also contains a transcript-first pilot corpus scaffold under [`data/corpus/`](data/corpus/):
- strict manifest rows with explicit transcript/audio/video verification fields
- committed transcript copies for a 20-call pilot set
- retrieval-ready artifacts such as `transcript_sectioned.json`, `qa_pairs.json`, `event_chunks.jsonl`, and `evidence_objects.jsonl`
- a local vector baseline at `data/corpus/retrieval/pilot_event_index/`

Rebuild it with:

```bash
PYTHONPATH=src python3 scripts/build_pilot_corpus.py --target-count 20 --embedding-provider hashing
PYTHONPATH=src python3 scripts/validate_pilot_corpus.py
```

Current pilot verification counts:
- transcript verified: `20`
- audio verified: `7`
- video verified: `0`

Those counts are intentionally strict. Transcript-backed evidence remains canonical, audio is only marked verified when committed derived review outputs exist, and video stays unverified until a real local video asset or replay artifact is present.

## What Makes It Credible
- Frozen labels are committed under [`data/gold_guidance_calls/`](data/gold_guidance_calls/).
- Current evaluation checkpoints are documented in [`docs/evaluation-summary.md`](docs/evaluation-summary.md).
- The canonical LLY proof bundle is committed under [`outputs/LLY_2025_Q2_call08/`](outputs/LLY_2025_Q2_call08/).
- The repo keeps explicit boundaries around what is demonstrated, partial, and unproven in [`docs/current-status.md`](docs/current-status.md) and [`docs/portfolio-proof.md`](docs/portfolio-proof.md).

Current repo-level checkpoints:
- frozen benchmark agreement: `9/9`
- unseen holdout agreement: `7/7`
- watchlist-derived unseen holdout agreement: `7/7`
- behavior rule-QA set: `58/58`

These numbers support deterministic review-tool positioning only. They do not establish predictive edge, statistical significance, or trading performance.

## Deterministic-First Boundary
- Transcript-backed deterministic artifacts are the source of truth.
- Audio, NLP, and video outputs are supporting layers only.
- Optional model sidecars do not overwrite deterministic labels or benchmark truth.
- Review confidence is confidence in the interpretation of available evidence, not investment confidence.
- The repo should be presented as workflow and evidence-packaging infrastructure, not as hidden-state inference.

## Local Review Shell
The main local shell is served by `app/site_server.py`:

```bash
PYTHONPATH=src PORT=7872 python app/site_server.py
```

It is useful for walkthroughs and product demos, but the canonical portfolio proof still lives in the checked-in LLY output bundle and supporting docs linked above.

## Repo Structure
- `app/`: local review shell
- `data/corpus/`: transcript-first pilot corpus manifests, normalized transcripts, retrieval artifacts, and corpus reports
- `data/gold_guidance_calls/`: frozen benchmark labels and source manifests
- `docs/`: demo path, current status, evaluation notes, and proof framing
- `outputs/LLY_2025_Q2_call08/`: canonical recruiter-facing proof bundle
- `scripts/`: verification and portfolio-proof helpers
- `src/earnings_call_sentiment/`: CLI and extraction pipeline

## Additional References
- [`docs/demo-path.md`](docs/demo-path.md)
- [`docs/portfolio-proof.md`](docs/portfolio-proof.md)
- [`docs/current-status.md`](docs/current-status.md)
- [`docs/evaluation-summary.md`](docs/evaluation-summary.md)
- [`docs/evidence-map.md`](docs/evidence-map.md)
- [`docs/pilot-corpus.md`](docs/pilot-corpus.md)

## Why This Matters
For technical pre-sales, workflow design, and AI-systems conversations, this repo shows a useful pattern:
- start with deterministic extraction
- preserve auditable intermediate artifacts
- keep optional model layers additive
- make non-claims explicit
- give reviewers a reproducible proof path instead of a vague product story
