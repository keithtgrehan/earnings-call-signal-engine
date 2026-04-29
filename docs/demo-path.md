# Demo Path

## Canonical Case
Use `LLY_2025_Q2_call08`.

Why this case:
- it has a frozen benchmark label in the committed gold package
- it has a committed deterministic output bundle in `outputs/LLY_2025_Q2_call08/`
- it is easy to explain quickly: transcript-backed reviewer artifacts, uncertainty cues, scorecard routing, and explicit sidecar boundaries
- the benchmark note records imperfect ASR quality, which makes it a useful credibility example instead of a polished-only demo

## One-Command Proof
```bash
python scripts/verify_outputs.py --out-dir outputs/LLY_2025_Q2_call08 --require-run-meta
```

Optional full check:
```bash
make portfolio-ci
```

## Open These Files In Order
1. `outputs/LLY_2025_Q2_call08/report.md`
   Start here for the reviewer-facing summary and strongest evidence snippets.
2. `outputs/LLY_2025_Q2_call08/metrics.json`
   This is the machine-readable scorecard and category summary.
3. `outputs/LLY_2025_Q2_call08/guidance.csv`
   Use this to inspect extracted guidance rows directly.
4. `outputs/LLY_2025_Q2_call08/transcript.txt`
   This is the underlying review truth for quoted evidence.
5. `outputs/LLY_2025_Q2_call08/uncertainty_signals.csv` and `outputs/LLY_2025_Q2_call08/analyst_skepticism.csv`
   Open these after the transcript-first pass to inspect the deterministic behavior layer.
6. `outputs/LLY_2025_Q2_call08/audio_behavior_summary.json` and `outputs/LLY_2025_Q2_call08/multimodal_support_summary.json`
   These show how supporting layers are kept additive rather than label-defining.
7. [labels.csv](../data/gold_guidance_calls/labels.csv)
   Check the `call08` row to confirm the frozen benchmark label and the conservative note about ASR quality.

## Two-Minute Talk Track
- This repo turns one earnings call into deterministic review artifacts instead of a free-form summary.
- The canonical proof case is Eli Lilly because the benchmark row is frozen, the output bundle is committed, and the limitation note is visible in-repo.
- The reviewer can move from report to metrics to raw transcript-backed evidence without leaving the repo.
- Audio and multimodal summaries exist, but they stay supportive only and do not overwrite deterministic review truth.
- The point of the walkthrough is auditable workflow design, not claiming that every downstream revision label is already production-complete.

## Boundaries
- This is a review workflow, not a trading system.
- The sidecar layers are additive only.
- The benchmark package is small and conservative by design.
