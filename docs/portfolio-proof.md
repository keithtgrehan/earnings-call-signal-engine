# Portfolio Proof

## Canonical Proof Case
The canonical recruiter-facing case is `LLY_2025_Q2_call08`.

It is the cleanest proof path because it combines:
- a frozen benchmark label
- a committed deterministic artifact bundle
- a visible benchmark note about imperfect ASR quality, which keeps the demo honest

## What Goes In
- source transcript text from [`data/gold_guidance_calls/raw_calls/LLY_2025_Q2_call08.txt`](../data/gold_guidance_calls/raw_calls/LLY_2025_Q2_call08.txt)
- frozen benchmark metadata from [`data/gold_guidance_calls/labels.csv`](../data/gold_guidance_calls/labels.csv), where `call08` is labeled `raised` with a conservative confidence note because the ASR text is imperfect
- deterministic pipeline stages that score chunks and extract guidance, tone, and behavior rows

## What Comes Out
- reviewer report: `outputs/LLY_2025_Q2_call08/report.md`
- structured scorecard: `outputs/LLY_2025_Q2_call08/metrics.json`
- extracted guidance rows: `outputs/LLY_2025_Q2_call08/guidance.csv`
- uncertainty and skepticism rows: `outputs/LLY_2025_Q2_call08/uncertainty_signals.csv`, `outputs/LLY_2025_Q2_call08/analyst_skepticism.csv`
- supporting summaries: `outputs/LLY_2025_Q2_call08/audio_behavior_summary.json`, `outputs/LLY_2025_Q2_call08/multimodal_support_summary.json`

## Claim To Evidence Map

| Claim | Exact evidence | Why it matters |
| --- | --- | --- |
| The repo is transcript-first and deterministic-first. | [`README.md`](../README.md), [`docs/current-status.md`](current-status.md), `outputs/LLY_2025_Q2_call08/transcript.txt` | The review truth is inspectable and local. |
| A frozen benchmark label exists in-repo. | [`data/gold_guidance_calls/labels.csv`](../data/gold_guidance_calls/labels.csv), [`data/gold_guidance_calls/raw_calls/LLY_2025_Q2_call08.txt`](../data/gold_guidance_calls/raw_calls/LLY_2025_Q2_call08.txt) | The proof case is tied to a committed label package, not a verbal claim. |
| The repo produces auditable reviewer outputs. | `outputs/LLY_2025_Q2_call08/report.md`, `outputs/LLY_2025_Q2_call08/metrics.json`, `outputs/LLY_2025_Q2_call08/guidance.csv` | A reviewer can move from summary to structured evidence. |
| Deterministic behavior cues are visible as files, not hidden scoring. | `outputs/LLY_2025_Q2_call08/uncertainty_signals.csv`, `outputs/LLY_2025_Q2_call08/analyst_skepticism.csv` | The repo exposes exactly what the reviewer is meant to inspect. |
| Supporting layers are explicitly bounded. | `outputs/LLY_2025_Q2_call08/audio_behavior_summary.json`, `outputs/LLY_2025_Q2_call08/multimodal_support_summary.json`, [`docs/evaluation-summary.md`](evaluation-summary.md) | Optional layers add context without replacing deterministic truth. |

## Deterministic-First Boundary
- Deterministic transcript-backed artifacts are canonical.
- The scorecard is a presentation layer over deterministic evidence.
- Audio, NLP, and video outputs are supporting only.
- The repo does not claim predictive lift, trading edge, or statistical significance.

## Why This Is Credible Portfolio Material
- It shows workflow design, not just model experimentation.
- It demonstrates auditable outputs and bounded claims.
- It keeps optional model/multimodal work separate from the canonical proof path.
- It gives a recruiter or interviewer a short, repeatable demo sequence inside the repo.

## Limitations
- The benchmark package is still small.
- The proof case supports review-tool positioning, not predictive claims.
- The benchmark row is explicitly conservative about ASR quality, so this case is better for demonstrating auditable workflow than for marketing directional precision.
- Guidance revision matching is still partial in the committed bundle and should be presented as a next-step capability rather than current headline proof.
- Multimodal coverage remains partial and should be presented conservatively.
