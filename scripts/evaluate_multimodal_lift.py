#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _render_protocol() -> str:
    return """# Multimodal Evaluation Protocol

## Purpose

Evaluate whether optional audio or video review cues improve reviewer usefulness beyond the transcript-only deterministic baseline.

## Labels

- uncertainty
- hedging
- guidance change
- analyst pressure
- evasive answer
- reassurance
- contradiction
- sentiment shift
- escalation risk

## Baselines

- transcript-first deterministic review
- transcript + audio sidecar
- transcript + audio + video sidecar

## Metrics

- precision
- recall
- f1
- false_positive_rate
- evidence_citation_quality
- time_to_first_useful_signal
- reviewer_clarity_rating
- reviewer_actionability_rating
- incremental_lift_over_transcript_only

## Required Gold Labels

- per-case review labels
- evidence spans or windows
- reviewer timing measurements
- reviewer clarity/actionability ratings

## Review Process

1. Run transcript-only review.
2. Run transcript + sidecar review on the same case set.
3. Capture timing, evidence quality, and reviewer ratings.
4. Compare lift only when the same tasks and labels exist for both conditions.

## Pilot Case Schema

- `transcript_text`
- `expected_signal_family`
- `expected_review_action`
- `audio_file`
- `video_file`
- `transcript_evidence`
- `audio_expected_cues`
- `video_expected_cues`
- `status`
- `limitations`

## Success Criteria

- improved reviewer speed without loss of evidence quality
- improved evidence traceability
- lower false positives than a naive sidecar interpretation

## What Counts As Real Multimodal Lift

- the same case has transcript-only and transcript-plus-media review results
- audio or video exists locally and is aligned to the transcript evidence window
- reviewer usefulness improves without hiding the underlying transcript rationale

## Minimum Evidence Before Any Claim

- committed aligned media or approved local media roots
- gold review labels for the same cases
- transcript-first baseline results
- sidecar results on the same evaluation cases
- clear reviewer timing and evidence-quality notes

## What Counts As Failure

- sidecars create confident claims without transcript support
- false positives rise without reviewer benefit
- reviewers cannot trace the extra signals back to usable evidence
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a scaffold multimodal evaluation protocol until aligned fixtures exist."
    )
    parser.add_argument(
        "--status-out",
        default=str(ROOT / "data" / "multimodal_research" / "evaluation_status.json"),
        help="Path to the JSON status output.",
    )
    parser.add_argument(
        "--protocol-out",
        default=str(ROOT / "docs" / "multimodal-evaluation-protocol.md"),
        help="Path to the Markdown protocol output.",
    )
    args = parser.parse_args(argv)

    status_out = Path(args.status_out)
    protocol_out = Path(args.protocol_out)
    status_out.parent.mkdir(parents=True, exist_ok=True)
    protocol_out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "status": "scaffold_only",
        "transcript_only_canonical": True,
        "multimodal_fixture_count": 0,
        "reason": "No aligned multimodal fixtures with gold reviewer labels are committed in the current Signal Engine 2.0 path.",
        "supported_metrics": [
            "precision",
            "recall",
            "f1",
            "false_positive_rate",
            "evidence_citation_quality",
            "time_to_first_useful_signal",
            "reviewer_clarity_rating",
            "reviewer_actionability_rating",
            "incremental_lift_over_transcript_only",
        ],
        "next_step": [
            "Create a small aligned transcript+audio(+video) fixture set with gold review labels.",
            "Measure transcript-only review first.",
            "Only compare sidecar lift after the transcript-only baseline is stable.",
        ],
    }

    status_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    protocol_out.write_text(_render_protocol(), encoding="utf-8")

    print(json.dumps({"status": payload["status"], "status_out": str(status_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
