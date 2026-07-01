#!/usr/bin/env python3
"""Verify and register the VZ 2024 Q4 transcript/audio pair attempt."""

from __future__ import annotations

import argparse
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

from signal_engine.audio.schemas import AUDIO_REGISTRY_FIELDS  # noqa: E402
from tools.first30_transcript_common import (  # noqa: E402
    APPROVAL_REF,
    DESKTOP_WORKSPACE,
    MANUAL_TRANSCRIPT_REGISTRY_FIELDS,
    MANUAL_TRANSCRIPT_REGISTRY_PATH,
    dedupe_registry_rows,
    fetch_url,
    file_sha256,
    looks_like_vendor_raw,
    parse_downloaded_transcript,
    read_csv,
    registry_row_from_parsed,
    text_sha256,
    write_csv,
    write_json,
)

FULL_TRANSCRIPT_URL = "https://www.verizon.com/about/sites/default/files/2025-01/VZ_4Q2024_Business_Update_Transcript_012425F.pdf"
PREPARED_TRANSCRIPT_URL = "https://www.verizon.com/about/sites/default/files/2025-01/VZ_4Q2024_ER_Transcript_012425_0.pdf"
PREPARED_AUDIO_URL = "https://www.verizon.com/about/sites/default/files/react_static/2500224Q24-Earnings-Recording.mp3"

PAIR_MANIFEST_FIELDS = [
    "pair_id",
    "case_id",
    "ticker",
    "full_transcript_url",
    "prepared_transcript_url",
    "audio_url",
    "full_transcript_local_path",
    "full_transcript_sha256",
    "full_transcript_text_path",
    "full_transcript_text_sha256",
    "prepared_transcript_local_path",
    "prepared_transcript_sha256",
    "prepared_transcript_text_path",
    "prepared_transcript_text_sha256",
    "audio_local_path",
    "audio_sha256",
    "source_relation",
    "pair_status",
    "review_required",
    "asr_ready",
    "commit_allowed",
    "training_allowed",
    "raw_assets_committed",
    "notes",
]

PAIR_OUT = ROOT / "data" / "acquisition" / "vz_2024_q4_pair_manifest.csv"
PAIR_REPORT = ROOT / "reports" / "acquisition" / "vz_2024_q4_pair_status.md"
ACQ_AUDIO_REGISTRY = ROOT / "data" / "acquisition" / "audio_registry.csv"
MANUAL_AUDIO_REGISTRY = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"


def _asset_path(workspace: Path, kind: str, suffix: str) -> Path:
    return workspace / "VZ_Verizon_Communications_Inc" / "vz_2024_q4" / kind / f"vz_2024_q4_{kind}{suffix}"


def _download(url: str, path: Path) -> tuple[Path, str, int, str]:
    payload, content_type = fetch_url(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path, file_sha256(path), len(payload), content_type


def _parse_pdf(url: str, raw_path: Path, payload_path_label: str) -> dict[str, str]:
    payload = raw_path.read_bytes()
    text, parse_status, parser = parse_downloaded_transcript(raw_path, payload, "application/pdf")
    text_path = raw_path.with_name(raw_path.stem + "_parsed.txt")
    text_digest = ""
    if parse_status == "parsed":
        if looks_like_vendor_raw(text):
            return {
                f"{payload_path_label}_text_path": "",
                f"{payload_path_label}_text_sha256": "",
                f"{payload_path_label}_parse_status": "blocked_vendor_marker",
                f"{payload_path_label}_parser": parser,
                "source_url": url,
            }
        text_path.write_text(text, encoding="utf-8")
        text_digest = text_sha256(text)
    return {
        f"{payload_path_label}_text_path": str(text_path) if text_digest else "",
        f"{payload_path_label}_text_sha256": text_digest,
        f"{payload_path_label}_parse_status": parse_status,
        f"{payload_path_label}_parser": parser,
        "source_url": url,
    }


def _merge_audio_registry(row: dict[str, str]) -> None:
    rows = {existing.get("audio_asset_id", ""): existing for existing in read_csv(ACQ_AUDIO_REGISTRY)}
    rows[row["audio_asset_id"]] = row
    write_csv(ACQ_AUDIO_REGISTRY, [rows[key] for key in sorted(rows)], AUDIO_REGISTRY_FIELDS)


def _merge_manual_audio_registry(row: dict[str, str]) -> None:
    rows = {existing.get("case_id", ""): existing for existing in read_csv(MANUAL_AUDIO_REGISTRY)}
    rows[row["case_id"]] = row
    write_csv(MANUAL_AUDIO_REGISTRY, [rows[key] for key in sorted(rows)], MANUAL_TRANSCRIPT_REGISTRY_FIELDS)


def verify_vz_pair(*, workspace: Path = DESKTOP_WORKSPACE, out_path: Path = PAIR_OUT) -> dict[str, Any]:
    errors: list[str] = []
    full_raw = _asset_path(workspace, "transcript", "_full_webcast.pdf")
    prepared_raw = _asset_path(workspace, "transcript", "_prepared.pdf")
    audio_raw = _asset_path(workspace, "audio", "_prepared_audio.mp3")
    try:
        _download(FULL_TRANSCRIPT_URL, full_raw)
    except Exception as exc:  # pragma: no cover - network-dependent
        errors.append(f"full_transcript_download_error:{type(exc).__name__}")
    try:
        _download(PREPARED_TRANSCRIPT_URL, prepared_raw)
    except Exception as exc:  # pragma: no cover - network-dependent
        errors.append(f"prepared_transcript_download_error:{type(exc).__name__}")
    try:
        _download(PREPARED_AUDIO_URL, audio_raw)
    except Exception as exc:  # pragma: no cover - network-dependent
        errors.append(f"prepared_audio_download_error:{type(exc).__name__}")
    full_sha = file_sha256(full_raw) if full_raw.exists() else ""
    prepared_sha = file_sha256(prepared_raw) if prepared_raw.exists() else ""
    audio_sha = file_sha256(audio_raw) if audio_raw.exists() else ""
    full_parse = _parse_pdf(FULL_TRANSCRIPT_URL, full_raw, "full_transcript") if full_raw.exists() else {}
    prepared_parse = _parse_pdf(PREPARED_TRANSCRIPT_URL, prepared_raw, "prepared_transcript") if prepared_raw.exists() else {}
    source_relation = "prepared_audio_vs_full_transcript"
    full_blocked = full_parse.get("full_transcript_parse_status") == "blocked_vendor_marker"
    prepared_blocked = prepared_parse.get("prepared_transcript_parse_status") == "blocked_vendor_marker"
    if full_blocked:
        errors.append("full_transcript_vendor_copyright_marker_detected")
    if prepared_blocked:
        errors.append("prepared_transcript_vendor_copyright_marker_detected")
    if full_blocked:
        pair_status = "blocked_vendor_full_transcript"
    elif prepared_blocked:
        pair_status = "blocked_vendor_prepared_transcript"
    else:
        pair_status = "matched_partial" if full_sha and prepared_sha and audio_sha else "blocked_incomplete"
    review_required = "true"
    asr_ready = "true" if audio_sha else "false"
    provenance = workspace / "VZ_Verizon_Communications_Inc" / "vz_2024_q4" / "metadata" / "vz_pair_provenance.json"
    write_json(
        provenance,
        {
            "case_id": "vz_2024_q4",
            "full_transcript_url": FULL_TRANSCRIPT_URL,
            "prepared_transcript_url": PREPARED_TRANSCRIPT_URL,
            "audio_url": PREPARED_AUDIO_URL,
            "full_transcript_local_path": str(full_raw) if full_raw.exists() else "",
            "prepared_transcript_local_path": str(prepared_raw) if prepared_raw.exists() else "",
            "audio_local_path": str(audio_raw) if audio_raw.exists() else "",
            "source_relation": source_relation,
            "pair_status": pair_status,
            "commit_allowed": False,
            "training_allowed": False,
            "raw_assets_committed": False,
            "approval_ref": APPROVAL_REF,
            "errors": errors,
        },
    )
    if full_parse.get("full_transcript_text_sha256"):
        row = {
            "case_id": "vz_2024_q4",
            "ticker": "VZ",
            "company_name": "Verizon Communications Inc.",
            "source_url": FULL_TRANSCRIPT_URL,
            "approval_ref": APPROVAL_REF,
        }
        registry_row = registry_row_from_parsed(row, Path(full_parse["full_transcript_text_path"]), full_parse["full_transcript_text_sha256"], provenance)
        final_registry = dedupe_registry_rows(read_csv(MANUAL_TRANSCRIPT_REGISTRY_PATH), [registry_row])
        write_csv(MANUAL_TRANSCRIPT_REGISTRY_PATH, final_registry, MANUAL_TRANSCRIPT_REGISTRY_FIELDS)
    if audio_sha:
        audio_row = {
            "audio_asset_id": "vz_2024_q4_audio",
            "case_id": "vz_2024_q4",
            "ticker": "VZ",
            "local_path": str(audio_raw),
            "sha256": audio_sha,
            "source_url": PREPARED_AUDIO_URL,
            "rights_status": "safe_to_download",
            "eval_allowed": "true",
            "commit_allowed": "false",
            "training_allowed": "false",
            "approval_ref": APPROVAL_REF,
            "raw_audio_committed": "false",
            "ffprobe_status": "not_run",
            "duration_sec": "",
            "sample_rate_hz": "",
            "channels": "",
            "asr_status": "todo_local_asr_not_run",
            "asr_text_path": "",
            "raw_asr_committed": "false",
            "notes": "Prepared earnings audio; not full webcast Q&A audio.",
        }
        _merge_audio_registry(audio_row)
        _merge_manual_audio_registry(
            {
                "case_id": "vz_2024_q4",
                "ticker": "VZ",
                "company_name": "Verizon Communications Inc.",
                "asset_type": "audio",
                "local_path": str(audio_raw),
                "sha256": audio_sha,
                "source_url": PREPARED_AUDIO_URL,
                "provenance_path": str(provenance),
                "rights_status": "safe_to_download",
                "eval_allowed": "true",
                "commit_allowed": "false",
                "training_allowed": "false",
                "approval_ref": APPROVAL_REF,
                "registered_timestamp": __import__("tools.first30_transcript_common", fromlist=["now_iso"]).now_iso(),
                "notes": "Prepared audio only; source_relation=prepared_audio_vs_full_transcript.",
            }
        )
    manifest_row = {
        "pair_id": "vz_2024_q4_prepared_audio_full_transcript",
        "case_id": "vz_2024_q4",
        "ticker": "VZ",
        "full_transcript_url": FULL_TRANSCRIPT_URL,
        "prepared_transcript_url": PREPARED_TRANSCRIPT_URL,
        "audio_url": PREPARED_AUDIO_URL,
        "full_transcript_local_path": str(full_raw) if full_raw.exists() else "",
        "full_transcript_sha256": full_sha,
        "full_transcript_text_path": full_parse.get("full_transcript_text_path", ""),
        "full_transcript_text_sha256": full_parse.get("full_transcript_text_sha256", ""),
        "prepared_transcript_local_path": str(prepared_raw) if prepared_raw.exists() else "",
        "prepared_transcript_sha256": prepared_sha,
        "prepared_transcript_text_path": prepared_parse.get("prepared_transcript_text_path", ""),
        "prepared_transcript_text_sha256": prepared_parse.get("prepared_transcript_text_sha256", ""),
        "audio_local_path": str(audio_raw) if audio_raw.exists() else "",
        "audio_sha256": audio_sha,
        "source_relation": source_relation,
        "pair_status": pair_status,
        "review_required": review_required,
        "asr_ready": asr_ready,
        "commit_allowed": "false",
        "training_allowed": "false",
        "raw_assets_committed": "false",
        "notes": (
            "Prepared MP3 is registered as partial support only; it is not treated as full-call Q&A audio. "
            "Full transcript is blocked if vendor copyright markers are detected."
        ),
    }
    write_csv(out_path, [manifest_row], PAIR_MANIFEST_FIELDS)
    audit = workspace / "_audit" / "vz_2024_q4_pair_status.csv"
    write_csv(audit, [manifest_row], PAIR_MANIFEST_FIELDS)
    write_report(manifest_row, errors)
    return {
        "pair_status": pair_status,
        "source_relation": source_relation,
        "review_required": True,
        "asr_ready": asr_ready == "true",
        "errors": errors,
        "out_manifest": str(out_path),
        "desktop_audit": str(audit),
    }


def write_report(row: dict[str, str], errors: list[str]) -> None:
    lines = [
        "# VZ 2024 Q4 Pair Status",
        "",
        f"- Pair status: `{row['pair_status']}`",
        f"- Source relation: `{row['source_relation']}`",
        f"- Review required: `{row['review_required']}`",
        f"- ASR ready: `{row['asr_ready']}`",
        "- Raw assets committed: false",
        "- Training allowed: false",
        "- Full transcript is canonical; prepared audio is support only.",
        f"- Full transcript path: `{row['full_transcript_local_path']}`",
        f"- Prepared transcript path: `{row['prepared_transcript_local_path']}`",
        f"- Audio path: `{row['audio_local_path']}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- none")
    PAIR_REPORT.parent.mkdir(parents=True, exist_ok=True)
    PAIR_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify VZ 2024 Q4 transcript/audio pair.")
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    parser.add_argument("--out", type=Path, default=PAIR_OUT)
    args = parser.parse_args(argv)
    summary = verify_vz_pair(workspace=args.workspace, out_path=args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
