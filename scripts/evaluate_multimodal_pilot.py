#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.multimodal import extract_text_feature_set


def _load_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _render_status_markdown(payload: dict) -> str:
    status_counts = payload["status_counts"]
    lines = [
        "# Multimodal Pilot Status",
        "",
        "- transcript_only_seed: `{}`".format(status_counts.get("transcript_only_seed", 0)),
        "- ready_for_audio: `{}`".format(status_counts.get("ready_for_audio", 0)),
        "- ready_for_video: `{}`".format(status_counts.get("ready_for_video", 0)),
        "- complete: `{}`".format(status_counts.get("complete", 0)),
        "- cases_with_audio: `{}`".format(payload["cases_with_audio"]),
        "- cases_with_video: `{}`".format(payload["cases_with_video"]),
        "- transcript_signal_coverage: `{}`".format(payload["transcript_signal_coverage"]),
        "",
        "## Status",
        "",
        f"- can_measure_multimodal_lift: `{payload['can_measure_multimodal_lift']}`",
        f"- blocker: {payload['blocker']}",
        "",
        "## Why This Matters",
        "",
        "- The pilot schema is now ready for aligned transcript-plus-media collection.",
        "- Transcript-only review still works today, and the media fields remain optional sidecars.",
        "- No multimodal lift claim should be made until the same cases have aligned audio or video and gold review outcomes.",
        "",
        "## Boundaries",
        "",
        "- Audio and video remain supporting review cues only.",
        "- Signals are review aids, not claims about hidden emotion, deception, or internal state.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate the current multimodal pilot scaffold and report whether lift can be measured yet."
    )
    parser.add_argument(
        "--input-path",
        default=str(ROOT / "data" / "multimodal_research" / "multimodal_pilot_cases.jsonl"),
        help="Path to the multimodal pilot JSONL file.",
    )
    parser.add_argument(
        "--status-path",
        default=str(ROOT / "data" / "multimodal_research" / "multimodal_pilot_status.json"),
        help="Path to the JSON status output.",
    )
    parser.add_argument(
        "--report-path",
        default=str(ROOT / "docs" / "multimodal-pilot-status.md"),
        help="Path to the Markdown status report.",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input_path)
    rows = _load_rows(input_path)
    status_counts = dict(Counter(row["status"] for row in rows))
    cases_with_audio = sum(1 for row in rows if row.get("audio_file"))
    cases_with_video = sum(1 for row in rows if row.get("video_file"))
    cases_complete = status_counts.get("complete", 0)

    transcript_signal_coverage = 0
    transcript_signal_examples = []
    for row in rows:
        feature_set = extract_text_feature_set(
            row["transcript_text"],
            domain=row.get("domain"),
            source_path=row.get("source_file"),
        )
        if feature_set.signals:
            transcript_signal_coverage += 1
        transcript_signal_examples.append(
            {
                "id": row["id"],
                "signal_count": len(feature_set.signals),
                "matched_signals": [signal.signal_name for signal in feature_set.signals],
            }
        )

    can_measure_lift = cases_complete > 0 and cases_with_audio > 0 and cases_with_video > 0
    blocker = (
        "No aligned audio or video media is committed for the pilot cases yet, so multimodal lift cannot be measured honestly."
        if not can_measure_lift
        else ""
    )
    payload = {
        "status": "scaffold_only" if not can_measure_lift else "ready_for_measurement",
        "case_count": len(rows),
        "status_counts": status_counts,
        "cases_with_audio": cases_with_audio,
        "cases_with_video": cases_with_video,
        "cases_complete": cases_complete,
        "transcript_signal_coverage": transcript_signal_coverage,
        "can_measure_multimodal_lift": can_measure_lift,
        "blocker": blocker,
        "transcript_only_canonical": True,
        "transcript_signal_examples": transcript_signal_examples,
    }

    status_path = Path(args.status_path)
    report_path = Path(args.report_path)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path.write_text(_render_status_markdown(payload), encoding="utf-8")

    print(json.dumps({"status": payload["status"], "case_count": len(rows), "report_path": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
