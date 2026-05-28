from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "transcript_normalization_readiness.md"


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _line_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        start = cursor
        end = cursor + len(line)
        cursor = end
        stripped = line.strip()
        if stripped:
            spans.append((start, end, stripped))
    return spans


def _role_for_line(line: str) -> str:
    prefix = line.split(":", 1)[0].strip().lower() if ":" in line else ""
    if any(token in prefix for token in ("analyst", "operator", "question")):
        return "analyst_or_operator"
    if any(token in prefix for token in ("management", "executive", "ceo", "cfo", "answer")):
        return "management"
    return "unknown"


def section_spans(text: str) -> list[dict[str, Any]]:
    lower = text.lower()
    markers = []
    for section_type, pattern in (("prepared_remarks", "prepared remarks"), ("qa", "question-and-answer")):
        index = lower.find(pattern)
        if index >= 0:
            markers.append((index, section_type))
    markers.sort()
    sections: list[dict[str, Any]] = []
    for idx, (start, section_type) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(text)
        section_text = text[start:end]
        sections.append({"section_type": section_type, "start_char": start, "end_char": end, "text_sha256": sha256_text(section_text)})
    if not sections and text:
        sections.append({"section_type": "unknown", "start_char": 0, "end_char": len(text), "text_sha256": sha256_text(text)})
    return sections


def speaker_turn_spans(text: str) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for start, end, line in _line_spans(text):
        if ":" not in line:
            continue
        speaker = line.split(":", 1)[0].strip()
        turns.append(
            {
                "speaker_role": _role_for_line(line),
                "speaker_label_sha256": sha256_text(speaker),
                "start_char": start,
                "end_char": end,
                "text_sha256": sha256_text(line),
            }
        )
    return turns


def qa_pair_spans(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    pending_question: dict[str, Any] | None = None
    for turn in turns:
        if turn["speaker_role"] == "analyst_or_operator":
            pending_question = turn
            continue
        if turn["speaker_role"] == "management" and pending_question is not None:
            pair_seed = f"{pending_question['text_sha256']}|{turn['text_sha256']}"
            pairs.append(
                {
                    "question_start_char": pending_question["start_char"],
                    "question_end_char": pending_question["end_char"],
                    "answer_start_char": turn["start_char"],
                    "answer_end_char": turn["end_char"],
                    "pair_sha256": sha256_text(pair_seed),
                }
            )
            pending_question = None
    return pairs


def normalize_transcript_metadata(
    *,
    case_id: str,
    ticker: str,
    source_asset_id: str,
    source_type: str,
    rights_status: str,
    text: str,
    provenance: dict[str, Any] | None = None,
    source_sha256: str = "",
) -> dict[str, Any]:
    source_hash = source_sha256 or sha256_text(text)
    sections = section_spans(text)
    turns = speaker_turn_spans(text)
    return {
        "case_id": case_id,
        "ticker": ticker,
        "case_metadata": {"case_id": case_id, "ticker": ticker},
        "source_asset_id": source_asset_id,
        "source_sha256": source_hash,
        "text_sha256": sha256_text(text),
        "source_type": source_type,
        "rights_status": rights_status,
        "sections": sections,
        "speaker_turns": turns,
        "qa_pairs": qa_pair_spans(turns),
        "prepared_remarks": [section for section in sections if section["section_type"] == "prepared_remarks"],
        "provenance": provenance or {},
        "raw_text_committed": False,
    }


def run_dry_run(*, report_path: Path = DEFAULT_REPORT, synthetic_text: str | None = None) -> dict[str, Any]:
    text = synthetic_text or "Prepared remarks\nManagement: Synthetic dry run.\nQuestion-and-Answer\nAnalyst: Q?\nManagement: A."
    payload = normalize_transcript_metadata(
        case_id="dry_run_case",
        ticker="DRY",
        source_asset_id="dry_run_asset",
        source_type="manual_local",
        rights_status="approved_manual_local",
        text=text,
        provenance={"mode": "dry_run"},
    )
    serialized = json.dumps(payload, sort_keys=True)
    raw_phrase_serialized = text in serialized
    summary = {
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "sections": len(payload["sections"]),
        "speaker_turns": len(payload["speaker_turns"]),
        "qa_pairs": len(payload["qa_pairs"]),
        "raw_text_committed": payload["raw_text_committed"],
        "raw_phrase_serialized": raw_phrase_serialized,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# Transcript Normalization Readiness",
                "",
                f"- Sections detected: {summary['sections']}",
                f"- Speaker turns detected: {summary['speaker_turns']}",
                f"- Q&A pairs detected: {summary['qa_pairs']}",
                "- Source payload serialized into contract: false",
                "- Raw text committed: false",
                "- Output contract: hashes, spans, source references, and provenance only.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run normalized transcript contract readiness without serializing raw text.")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_dry_run(report_path=args.report_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
