#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.signal_baseline import (
    HUMAN_REVIEWED_LABELS_RELATIVE_PATH,
    load_supervised_examples,
)


PILOT_CASE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "pilot_support_dispute_audio_001",
        "source_label_id": "risk_support_dispute_001",
        "expected_review_action": "Escalate duplicate-charge dispute ownership and confirm a dated remediation plan.",
        "audio_expected_cues": [
            "Pause clustering before the agent response may signal a weak handoff or uncertainty.",
            "Intensity spikes around dispute language may help reviewers prioritize the case.",
        ],
        "video_expected_cues": [],
        "status": "ready_for_audio",
        "limitations": "Transcript evidence is already strong; audio would only add bounded review context.",
    },
    {
        "id": "pilot_sales_procurement_block_audio_001",
        "source_label_id": "risk_sales_procurement_block_001",
        "expected_review_action": "Prepare a concrete next-step package with pricing range, security packet, and dated follow-up.",
        "audio_expected_cues": [
            "Review for interruption or overlap when procurement blockers are raised.",
            "Review for longer pauses before the rep answers the objection.",
        ],
        "video_expected_cues": [],
        "status": "ready_for_audio",
        "limitations": "No call recording is committed, so lift cannot be measured yet.",
    },
    {
        "id": "pilot_sales_probably_audio_001",
        "source_label_id": "unc_sales_probably_001",
        "expected_review_action": "Replace hedged pricing language with a dated, concrete commercial next step.",
        "audio_expected_cues": [
            "Review for hesitation markers around the hedged promise.",
            "Review for speech-rate drop before the rep commits to specifics.",
        ],
        "video_expected_cues": [],
        "status": "ready_for_audio",
        "limitations": "The transcript already captures the hedge; audio would be supporting evidence only.",
    },
    {
        "id": "pilot_account_renewal_video_001",
        "source_label_id": "risk_account_vendor_risk_001",
        "expected_review_action": "Route to a renewal-risk review with ownership, timeline, and downgrade mitigation.",
        "audio_expected_cues": [],
        "video_expected_cues": [
            "If a meeting recording exists, review gaze shifts or posture changes only as bounded review cues around renewal pressure.",
            "If available, review visible engagement changes when downgrade or vendor-switch language appears.",
        ],
        "status": "ready_for_video",
        "limitations": "No video is committed; any future visual cues must remain secondary to the transcript.",
    },
    {
        "id": "pilot_account_recovery_video_001",
        "source_label_id": "opp_account_recovery_plan_001",
        "expected_review_action": "Track whether the named recovery owners and Friday delivery commitment are met.",
        "audio_expected_cues": [],
        "video_expected_cues": [
            "If a recorded review exists, inspect visible engagement only as a follow-up cue around ownership language.",
            "Do not infer hidden confidence; use any visual cue only to prioritize manual review.",
        ],
        "status": "ready_for_video",
        "limitations": "Transcript commitments remain canonical and auditable without media.",
    },
    {
        "id": "pilot_sales_plan_transcript_001",
        "source_label_id": "opp_sales_plan_commitment_001",
        "expected_review_action": "Track the Tuesday proposal commitment in the deal follow-up.",
        "audio_expected_cues": [],
        "video_expected_cues": [],
        "status": "transcript_only_seed",
        "limitations": "The transcript is already sufficient for the core review task.",
    },
    {
        "id": "pilot_support_resolution_transcript_001",
        "source_label_id": "opp_support_resolution_seed_001",
        "expected_review_action": "Log the resolution-positive case and verify whether the same pattern generalizes.",
        "audio_expected_cues": [],
        "video_expected_cues": [],
        "status": "transcript_only_seed",
        "limitations": "This case is useful for contrast, not for proving broader performance.",
    },
    {
        "id": "pilot_support_waiting_transcript_001",
        "source_label_id": "unc_support_waiting_update_001",
        "expected_review_action": "Flag the vague follow-up and ask for a concrete owner and timing commitment.",
        "audio_expected_cues": [],
        "video_expected_cues": [],
        "status": "transcript_only_seed",
        "limitations": "The transcript captures the unresolved timing gap without needing media.",
    },
    {
        "id": "pilot_sales_status_transcript_001",
        "source_label_id": "neut_sales_status_full_001",
        "expected_review_action": "Treat as process status only unless later turns add friction or commitments.",
        "audio_expected_cues": [],
        "video_expected_cues": [],
        "status": "transcript_only_seed",
        "limitations": "Neutral operational updates are included to keep the pilot schema balanced.",
    },
    {
        "id": "pilot_account_status_transcript_001",
        "source_label_id": "neut_account_status_full_001",
        "expected_review_action": "Log as scheduling context only and avoid over-interpreting it as risk.",
        "audio_expected_cues": [],
        "video_expected_cues": [],
        "status": "transcript_only_seed",
        "limitations": "This case is useful for false-positive control in future pilots.",
    },
)


def build_pilot_cases(root: Path | None = None) -> list[dict[str, Any]]:
    repo_root = root or ROOT
    label_path = repo_root / HUMAN_REVIEWED_LABELS_RELATIVE_PATH
    label_rows = {
        row["id"]: row
        for row in load_supervised_examples(label_path)
    }
    cases = []
    for spec in PILOT_CASE_SPECS:
        label_row = label_rows[spec["source_label_id"]]
        cases.append(
            {
                "id": spec["id"],
                "domain": label_row["domain"],
                "transcript_text": label_row["text"],
                "expected_signal_family": label_row["signal_family"],
                "expected_review_action": spec["expected_review_action"],
                "audio_file": None,
                "video_file": None,
                "transcript_evidence": list(label_row.get("evidence_terms") or []),
                "audio_expected_cues": list(spec["audio_expected_cues"]),
                "video_expected_cues": list(spec["video_expected_cues"]),
                "status": spec["status"],
                "limitations": spec["limitations"],
                "source_label_id": label_row["id"],
                "source_file": label_row["source_file"],
            }
        )
    return cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a tiny multimodal pilot case scaffold from committed local transcript seeds."
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "multimodal_research" / "multimodal_pilot_cases.jsonl"),
        help="Path to the JSONL pilot-case output.",
    )
    args = parser.parse_args(argv)

    rows = build_pilot_cases()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "ok", "out": str(out_path), "case_count": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
