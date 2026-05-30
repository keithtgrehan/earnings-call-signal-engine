#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.asr_backends import detect_local_asr_backend, ffmpeg_status, probe_audio
from signal_engine.audio.asr_manifest import build_asr_manifest_row
from signal_engine.audio.schemas import ASR_MANIFEST_FIELDS, ASR_SEGMENT_FIELDS

DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
DEFAULT_AUDIO_REGISTRY = ROOT / "data" / "acquisition" / "audio_registry.csv"
DEFAULT_ASR_MANIFEST = ROOT / "data" / "acquisition" / "asr_run_manifest.csv"
DEFAULT_SEGMENT_MANIFEST = ROOT / "data" / "acquisition" / "asr_segment_manifest.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "asr_execution_status.md"


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


def _asr_dir(workspace: Path, case_id: str) -> Path:
    return workspace / "VZ_Verizon_Communications_Inc" / case_id / "asr"


def _run_openai_whisper(audio_path: Path, out_dir: Path, model: str, timeout: int) -> tuple[str, Path | None, Path | None, str]:
    executable = detect_local_asr_backend("openai-whisper").get("executable") or "whisper"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                executable,
                str(audio_path),
                "--model",
                model,
                "--output_dir",
                str(out_dir),
                "--output_format",
                "all",
                "--fp16",
                "False",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - dependency/runtime dependent
        return "asr_failed", None, None, f"{type(exc).__name__}: {exc}"
    stem = audio_path.stem
    txt = out_dir / f"{stem}.txt"
    json_path = out_dir / f"{stem}.json"
    return "complete" if txt.exists() else "asr_failed_no_text", txt if txt.exists() else None, json_path if json_path.exists() else None, ""


def _segments_from_whisper_json(json_path: Path | None, case_id: str, audio_asset_id: str) -> list[dict[str, str]]:
    if not json_path or not json_path.exists():
        return []
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for index, segment in enumerate(payload.get("segments") or [], start=1):
        text = str(segment.get("text", ""))
        digest = "sha256:" + __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()
        rows.append(
            {
                "segment_id": f"{case_id}_{index:05d}",
                "case_id": case_id,
                "audio_asset_id": audio_asset_id,
                "start_time_sec": str(segment.get("start", "")),
                "end_time_sec": str(segment.get("end", "")),
                "speaker": "",
                "text_sha256": digest,
                "raw_text_committed": "false",
            }
        )
    return rows


def run_local_asr_smoke(
    *,
    audio_registry: Path = DEFAULT_AUDIO_REGISTRY,
    workspace: Path = DEFAULT_WORKSPACE,
    out_manifest: Path = DEFAULT_ASR_MANIFEST,
    segment_manifest: Path = DEFAULT_SEGMENT_MANIFEST,
    backend_name: str = "",
    model: str = "tiny",
    timeout: int = 900,
) -> dict[str, Any]:
    audio_rows = [row for row in read_csv(audio_registry) if row.get("eval_allowed") == "true" and row.get("commit_allowed") == "false"]
    target = next((row for row in audio_rows if row.get("case_id") == "vz_2024_q4"), audio_rows[0] if audio_rows else None)
    backend = detect_local_asr_backend(backend_name)
    ffmpeg = ffmpeg_status()
    manifest_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, str]] = []
    status = "dependency_missing"
    notes = backend.get("install_instructions", "")
    if not target:
        status = "no_registered_audio"
        manifest_rows = []
    else:
        audio_path = Path(target.get("local_path", ""))
        probe = probe_audio(audio_path) if audio_path.exists() else {"ffprobe_status": "audio_missing"}
        can_run = backend["dependency_status"] in {"available", "available_python_package"} and ffmpeg["ffmpeg_status"] == "available" and audio_path.exists()
        asr_text_path = ""
        segments_path = ""
        if can_run and backend["backend"] == "openai-whisper" and backend.get("executable"):
            asr_dir = _asr_dir(workspace, target.get("case_id", "unknown"))
            status, txt_path, json_path, run_notes = _run_openai_whisper(audio_path, asr_dir, model, timeout)
            notes = run_notes or "openai-whisper local execution completed"
            if txt_path:
                asr_text_path = str(txt_path)
            segment_rows = _segments_from_whisper_json(json_path, target.get("case_id", ""), target.get("audio_asset_id", ""))
            if segment_rows:
                segments_path = str(segment_manifest)
        elif can_run:
            status = "dependency_available_runner_not_configured"
            notes = "Local ASR dependency detected but this smoke runner only executes the openai-whisper CLI without a custom model path."
        row = build_asr_manifest_row(
            case_id=target.get("case_id", ""),
            audio_asset_id=target.get("audio_asset_id", ""),
            audio_sha256=target.get("sha256", ""),
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
        "target_case_id": target.get("case_id", "") if target else "",
        "backend": backend,
        "ffmpeg": ffmpeg,
        "status": status,
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


def write_report(summary: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    backend = summary["backend"]
    lines = [
        "# ASR Execution Status",
        "",
        f"- Registered audio rows: {summary['registered_audio']}",
        f"- Target case: `{summary['target_case_id']}`",
        f"- Backend: `{backend.get('backend')}`",
        f"- Dependency status: `{backend.get('dependency_status')}`",
        f"- Run status: `{summary['status']}`",
        f"- ASR complete rows: {summary['asr_complete']}",
        f"- Segment rows: {summary['segment_rows']}",
        f"- Cloud ASR used: {str(summary['cloud_asr_used']).lower()}",
        f"- Raw ASR committed: {str(summary['raw_asr_committed']).lower()}",
        f"- Install instructions: {backend.get('install_instructions', '')}",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local ASR smoke if a local backend is available.")
    parser.add_argument("--backend", default="")
    parser.add_argument("--audio-registry", type=Path, default=DEFAULT_AUDIO_REGISTRY)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_ASR_MANIFEST)
    parser.add_argument("--segments-out", type=Path, default=DEFAULT_SEGMENT_MANIFEST)
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    payload = run_local_asr_smoke(
        audio_registry=args.audio_registry,
        workspace=args.workspace,
        out_manifest=args.out,
        segment_manifest=args.segments_out,
        backend_name=args.backend,
        model=args.model,
        timeout=args.timeout,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
