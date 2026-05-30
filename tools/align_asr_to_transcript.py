#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.alignment import alignment_row
from signal_engine.audio.schemas import AUDIO_ALIGNMENT_FIELDS


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


def build_alignment_manifest(*, audio_registry: Path, transcript_registry: Path, out_path: Path) -> dict[str, int]:
    transcripts = {row.get("case_id", ""): row for row in read_csv(transcript_registry)}
    rows: list[dict[str, str]] = []
    for audio in read_csv(audio_registry):
        transcript = transcripts.get(audio.get("case_id", ""))
        if not transcript:
            continue
        row = alignment_row(case_id=audio.get("case_id", ""), audio_sha256=audio.get("sha256", ""), transcript_sha256=transcript.get("sha256", ""))
        rows.append({field: str(row.get(field, "")) for field in AUDIO_ALIGNMENT_FIELDS})
    write_csv(out_path, rows)
    return {"alignment_rows": len(rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create ASR/transcript alignment TODO metadata without raw text.")
    parser.add_argument("--audio-registry", type=Path, default=ROOT / "data" / "acquisition" / "audio_registry.csv")
    parser.add_argument("--transcript-registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "acquisition" / "audio_alignment_manifest.csv")
    args = parser.parse_args(argv)
    print(build_alignment_manifest(audio_registry=args.audio_registry, transcript_registry=args.transcript_registry, out_path=args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
