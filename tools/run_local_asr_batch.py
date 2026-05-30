#!/usr/bin/env python3
"""Run local ASR over registered audio when a local backend is available."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.asr_backends import detect_local_asr_backend, ffmpeg_status, probe_audio  # noqa: E402
from signal_engine.audio.asr_manifest import build_asr_manifest_row  # noqa: E402
from signal_engine.audio.schemas import ASR_MANIFEST_FIELDS, ASR_SEGMENT_FIELDS  # noqa: E402
from tools.run_local_asr_smoke import _asr_dir, _run_faster_whisper, _run_openai_whisper, _segments_from_whisper_json, write_report  # noqa: E402

DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
DEFAULT_AUDIO_REGISTRY = ROOT / "data" / "acquisition" / "audio_registry.csv"
DEFAULT_ASR_MANIFEST = ROOT / "data" / "acquisition" / "asr_run_manifest.csv"
DEFAULT_SEGMENT_MANIFEST = ROOT / "data" / "acquisition" / "asr_segment_manifest.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: str(value).lower() if isinstance(value, bool) else value for key, value in row.items()})


def _ordered_audio_rows(path: Path) -> list[dict[str, str]]:
    rows = [row for row in read_csv(path) if row.get("eval_allowed") == "true" and row.get("commit_allowed") == "false"]
    return sorted(rows, key=lambda row: (0 if row.get("case_id") == "vz_2024_q4" else 1, row.get("case_id", "")))


def run_local_asr_batch(
    *,
    audio_registry: Path = DEFAULT_AUDIO_REGISTRY,
    workspace: Path = DEFAULT_WORKSPACE,
    out_manifest: Path = DEFAULT_ASR_MANIFEST,
    segment_manifest: Path = DEFAULT_SEGMENT_MANIFEST,
    backend_name: str = "",
    model: str = "tiny",
    timeout: int = 900,
    max_audio: int = 0,
) -> dict[str, Any]:
    audio_rows = _ordered_audio_rows(audio_registry)
    if max_audio > 0:
        audio_rows = audio_rows[:max_audio]
    backend = detect_local_asr_backend(backend_name)
    ffmpeg = ffmpeg_status()
    can_run = backend["dependency_status"] in {"available", "available_python_package"} and ffmpeg["ffmpeg_status"] == "available"
    manifest_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, str]] = []
    for audio in audio_rows:
        audio_path = Path(audio.get("local_path", ""))
        probe = probe_audio(audio_path) if audio_path.exists() else {"ffprobe_status": "audio_missing"}
        status = "dependency_missing"
        notes = backend.get("install_instructions", "")
        asr_text_path = ""
        segments_path = ""
        if not audio_path.exists():
            status = "audio_missing"
            notes = "Registered audio local_path is missing."
        elif can_run and backend["backend"] == "faster-whisper":
            asr_dir = _asr_dir(workspace, audio.get("case_id", "unknown"))
            status, txt_path, json_path, run_notes = _run_faster_whisper(audio_path, asr_dir, model, local_files_only=True)
            notes = run_notes or "faster-whisper local execution completed with a local/cached model"
            if txt_path:
                asr_text_path = str(txt_path)
            new_segments = _segments_from_whisper_json(json_path, audio.get("case_id", ""), audio.get("audio_asset_id", ""))
            segment_rows.extend(new_segments)
            if new_segments:
                segments_path = str(segment_manifest)
        elif can_run and backend["backend"] == "openai-whisper" and backend.get("executable"):
            asr_dir = _asr_dir(workspace, audio.get("case_id", "unknown"))
            status, txt_path, json_path, run_notes = _run_openai_whisper(audio_path, asr_dir, model, timeout)
            notes = run_notes or "openai-whisper local execution completed"
            if txt_path:
                asr_text_path = str(txt_path)
            new_segments = _segments_from_whisper_json(json_path, audio.get("case_id", ""), audio.get("audio_asset_id", ""))
            segment_rows.extend(new_segments)
            if new_segments:
                segments_path = str(segment_manifest)
        elif can_run:
            status = "dependency_available_runner_not_configured"
            notes = "Local ASR dependency detected, but batch runner has no configured local runner for that backend."
        row = build_asr_manifest_row(
            case_id=audio.get("case_id", ""),
            audio_asset_id=audio.get("audio_asset_id", ""),
            audio_sha256=audio.get("sha256", ""),
            engine=backend_name,
            status=status,
            asr_text_path=asr_text_path,
            segments_path=segments_path,
            notes=f"{notes}; ffprobe_status={probe.get('ffprobe_status', '')}",
        )
        manifest_rows.append(row)
    write_csv(out_manifest, manifest_rows, ASR_MANIFEST_FIELDS)
    write_csv(segment_manifest, segment_rows, ASR_SEGMENT_FIELDS)
    desktop_status = workspace / "_audit" / "asr_execution_status.json"
    desktop_status.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "registered_audio": len(audio_rows),
        "target_case_id": audio_rows[0].get("case_id", "") if audio_rows else "",
        "backend": backend,
        "ffmpeg": ffmpeg,
        "status": "complete" if any(row.get("status") == "complete" for row in manifest_rows) else ("no_registered_audio" if not audio_rows else manifest_rows[0].get("status", "dependency_missing")),
        "asr_complete": sum(1 for row in manifest_rows if row.get("status") == "complete"),
        "segment_rows": len(segment_rows),
        "cloud_asr_used": False,
        "raw_asr_committed": False,
        "out_manifest": str(out_manifest),
        "segment_manifest": str(segment_manifest),
        "desktop_status": str(desktop_status),
    }
    desktop_status.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local ASR over registered audio if local dependencies exist.")
    parser.add_argument("--backend", default="")
    parser.add_argument("--audio-registry", type=Path, default=DEFAULT_AUDIO_REGISTRY)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_ASR_MANIFEST)
    parser.add_argument("--segments-out", type=Path, default=DEFAULT_SEGMENT_MANIFEST)
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-audio", type=int, default=0)
    args = parser.parse_args(argv)
    summary = run_local_asr_batch(
        audio_registry=args.audio_registry,
        workspace=args.workspace,
        out_manifest=args.out,
        segment_manifest=args.segments_out,
        backend_name=args.backend,
        model=args.model,
        timeout=args.timeout,
        max_audio=args.max_audio,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
