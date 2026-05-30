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

from signal_engine.audio.schemas import AUDIO_RAG_OBJECT_FIELDS


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIO_RAG_OBJECT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def export_audio_objects(*, audio_registry: Path, alignment_manifest: Path, out_path: Path) -> dict[str, int]:
    audio_rows = {row.get("case_id", ""): row for row in read_csv(audio_registry)}
    rows: list[dict[str, str]] = []
    for alignment in read_csv(alignment_manifest):
        if alignment.get("alignment_status") != "aligned":
            continue
        audio = audio_rows.get(alignment.get("case_id", ""))
        if not audio:
            continue
        rows.append(
            {
                "audio_object_id": f"{alignment['alignment_id']}_audio_object",
                "case_id": alignment.get("case_id", ""),
                "audio_asset_id": alignment.get("audio_asset_id", ""),
                "transcript_chunk_id": "",
                "alignment_id": alignment.get("alignment_id", ""),
                "source_sha256": audio.get("sha256", ""),
                "rights_status": audio.get("rights_status", ""),
                "retrieval_ready": "true",
                "raw_audio_committed": "false",
                "raw_asr_committed": "false",
            }
        )
    write_csv(out_path, rows)
    return {"audio_objects": len(rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export audio retrieval objects only after transcript alignment.")
    parser.add_argument("--audio-registry", type=Path, default=ROOT / "data" / "acquisition" / "audio_registry.csv")
    parser.add_argument("--alignment-manifest", type=Path, default=ROOT / "data" / "acquisition" / "audio_alignment_manifest.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "retrieval" / "audio_retrieval_objects_manifest.csv")
    args = parser.parse_args(argv)
    print(export_audio_objects(audio_registry=args.audio_registry, alignment_manifest=args.alignment_manifest, out_path=args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
