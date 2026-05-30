#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.alignment import alignment_row, fuzzy_window_score, prepared_section
from signal_engine.audio.schemas import AUDIO_ALIGNMENT_FIELDS

DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
DEFAULT_ASR_MANIFEST = ROOT / "data" / "acquisition" / "asr_run_manifest.csv"
DEFAULT_PAIR_MANIFEST = ROOT / "data" / "acquisition" / "vz_2024_q4_pair_manifest.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "audio_transcript_alignment_manifest.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "audio_transcript_alignment_status.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIO_ALIGNMENT_FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_text(path: str) -> str:
    value = Path(path)
    if not value.exists():
        return ""
    return value.read_text(encoding="utf-8", errors="replace")


def _pair_row(pair_manifest: Path, case_id: str) -> dict[str, str]:
    for row in read_csv(pair_manifest):
        if row.get("case_id") == case_id:
            return row
    return {}


def build_alignment_manifest(
    *,
    audio_registry: Path,
    transcript_registry: Path,
    asr_manifest: Path,
    pair_manifest: Path,
    out_path: Path,
    workspace: Path = DEFAULT_WORKSPACE,
    threshold: float = 0.35,
) -> dict[str, Any]:
    transcripts = {row.get("case_id", ""): row for row in read_csv(transcript_registry)}
    asr_rows = {row.get("case_id", ""): row for row in read_csv(asr_manifest)}
    rows: list[dict[str, str]] = []
    for audio in read_csv(audio_registry):
        case_id = audio.get("case_id", "")
        transcript = transcripts.get(case_id)
        pair = _pair_row(pair_manifest, case_id)
        source_relation = pair.get("source_relation", "")
        if pair.get("prepared_transcript_text_path") and pair.get("audio_sha256") == audio.get("sha256", ""):
            transcript = {
                "local_path": pair.get("prepared_transcript_text_path", ""),
                "sha256": pair.get("prepared_transcript_text_sha256", ""),
            }
            source_relation = "prepared_audio_vs_prepared_transcript"
        if not transcript:
            continue
        asr = asr_rows.get(case_id, {})
        transcript_text = _read_text(transcript.get("local_path", ""))
        asr_text = _read_text(asr.get("asr_text_path", ""))
        partial = source_relation in {"prepared_audio_vs_full_transcript", "prepared_audio_vs_prepared_transcript"}
        review = partial
        status = "not_ready"
        method = ""
        score = 0.0
        start = 0
        end = 0
        matched = 0
        notes = "Alignment not run: transcript, audio, and local ASR text are required."
        if asr.get("status") == "complete" and transcript_text and asr_text:
            candidate_text = transcript_text
            offset = 0
            if partial:
                candidate_text, offset, _ = prepared_section(transcript_text)
            result = fuzzy_window_score(asr_text, candidate_text)
            score = float(result["score"])
            start = offset + int(result["start_char"])
            end = offset + int(result["end_char"])
            method = result["method"]
            matched = 1 if score >= threshold else 0
            status = "aligned" if matched else "below_threshold"
            notes = "Prepared-audio to prepared-transcript alignment candidate." if source_relation == "prepared_audio_vs_prepared_transcript" else ("Partial prepared-audio alignment candidate." if partial else "Full transcript alignment candidate.")
        elif asr.get("status"):
            status = f"not_ready_{asr.get('status')}"
        row = alignment_row(
            case_id=case_id,
            audio_sha256=audio.get("sha256", ""),
            transcript_sha256=transcript.get("sha256", ""),
            alignment_status=status,
            alignment_method=method,
            alignment_score=score,
            matched_span_count=matched,
            matched_start_char=start,
            matched_end_char=end,
            partial_alignment=partial,
            review_required=review,
            source_relation=source_relation,
            notes=notes,
        )
        rows.append({field: str(row.get(field, "")) for field in AUDIO_ALIGNMENT_FIELDS})
    write_csv(out_path, rows)
    audit = workspace / "_audit" / "audio_transcript_alignment_manifest.csv"
    write_csv(audit, rows)
    summary = {
        "alignment_rows": len(rows),
        "aligned_rows": sum(1 for row in rows if row.get("alignment_status") == "aligned"),
        "partial_alignment_rows": sum(1 for row in rows if row.get("partial_alignment") == "True"),
        "review_required_rows": sum(1 for row in rows if row.get("review_required") == "True"),
        "out_manifest": str(out_path),
        "desktop_audit": str(audit),
    }
    write_report(summary, rows)
    return summary


def write_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Audio Transcript Alignment Status",
        "",
        f"- Alignment rows: {summary['alignment_rows']}",
        f"- Aligned rows: {summary['aligned_rows']}",
        f"- Partial alignment rows: {summary['partial_alignment_rows']}",
        f"- Review-required rows: {summary['review_required_rows']}",
        "- Audio-only data used as transcript evidence: false",
        "",
        "## Rows",
        "",
    ]
    if rows:
        for row in rows:
            lines.append(
                f"- `{row.get('case_id')}` status={row.get('alignment_status')} "
                f"score={row.get('alignment_score')} partial={row.get('partial_alignment')}"
            )
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create ASR/transcript alignment TODO metadata without raw text.")
    parser.add_argument("--audio-registry", type=Path, default=ROOT / "data" / "acquisition" / "audio_registry.csv")
    parser.add_argument("--transcript-registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv")
    parser.add_argument("--asr-manifest", type=Path, default=DEFAULT_ASR_MANIFEST)
    parser.add_argument("--pair-manifest", type=Path, default=DEFAULT_PAIR_MANIFEST)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--threshold", type=float, default=0.35)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            build_alignment_manifest(
                audio_registry=args.audio_registry,
                transcript_registry=args.transcript_registry,
                asr_manifest=args.asr_manifest,
                pair_manifest=args.pair_manifest,
                out_path=args.out,
                workspace=args.workspace,
                threshold=args.threshold,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
