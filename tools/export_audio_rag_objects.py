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

from signal_engine.audio.schemas import AUDIO_RAG_OBJECT_FIELDS

REPORT_PATH = ROOT / "reports" / "acquisition" / "audio_rag_object_status.md"
DEFAULT_AUDIO_REGISTRY = ROOT / "data" / "acquisition" / "audio_registry.csv"
DEFAULT_ALIGNMENT_MANIFEST = ROOT / "data" / "acquisition" / "audio_transcript_alignment_manifest.csv"
DEFAULT_OUT = ROOT / "data" / "retrieval" / "audio_objects_manifest.csv"
DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")


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


def export_audio_objects(*, audio_registry: Path, alignment_manifest: Path, out_path: Path, workspace: Path = DEFAULT_WORKSPACE, threshold: float = 0.35) -> dict[str, Any]:
    audio_rows = {row.get("case_id", ""): row for row in read_csv(audio_registry)}
    rows: list[dict[str, str]] = []
    for alignment in read_csv(alignment_manifest):
        if alignment.get("alignment_status") != "aligned":
            continue
        try:
            score = float(alignment.get("alignment_score") or "0")
        except ValueError:
            score = 0.0
        if score < threshold:
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
    audit = workspace / "_audit" / "audio_rag_index.csv"
    write_csv(audit, rows)
    summary = {
        "audio_objects": len(rows),
        "retrieval_ready": sum(1 for row in rows if row.get("retrieval_ready") == "true"),
        "alignment_manifest": str(alignment_manifest),
        "out_manifest": str(out_path),
        "desktop_audit": str(audit),
        "status": "READY" if rows else "NOT_READY",
    }
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Audio RAG Object Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Audio objects: {summary['audio_objects']}",
        f"- Retrieval-ready objects: {summary['retrieval_ready']}",
        "- Requires registered audio, ASR text, matched transcript, and alignment score above threshold.",
        "- Audio-only data used as transcript evidence: false",
        "- Raw audio committed: false",
        "- Raw ASR committed: false",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export audio retrieval objects only after transcript alignment.")
    parser.add_argument("--audio-registry", type=Path, default=DEFAULT_AUDIO_REGISTRY)
    parser.add_argument("--alignment-manifest", type=Path, default=DEFAULT_ALIGNMENT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--threshold", type=float, default=0.35)
    args = parser.parse_args(argv)
    print(json.dumps(export_audio_objects(audio_registry=args.audio_registry, alignment_manifest=args.alignment_manifest, out_path=args.out, workspace=args.workspace, threshold=args.threshold), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
