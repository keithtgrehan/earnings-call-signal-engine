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

from signal_engine.adapters import optional_transformer_emotion
from signal_engine.multimodal import (
    build_multimodal_report,
    extract_audio_feature_set,
    extract_text_feature_set,
    extract_video_feature_set,
)
from signal_engine.pipeline import _load_records
from signal_engine.privacy import (
    redact_conversation,
    redact_pii_text,
    summarize_redactions,
)


def _text_from_record(record: dict[str, Any]) -> str:
    segments = record.get("transcript_segments") or record.get("messages") or []
    lines = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text") or segment.get("message") or segment.get("content") or "").strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def _load_text_input(path: Path, *, redact_pii: bool) -> tuple[str, dict[str, Any]]:
    if path.suffix.lower() in {".json", ".jsonl"}:
        records = _load_records(path)
        if not records:
            raise RuntimeError(f"No transcript records found in {path}")
        record = records[0]
        metadata = {"input_type": "conversation_record", "source_path": str(path)}
        if redact_pii:
            redacted = redact_conversation(record)
            metadata["pii_redaction"] = {
                "enabled": True,
                "summary": summarize_redactions(redacted["redactions"]),
            }
            return _text_from_record(redacted["conversation"]), metadata
        return _text_from_record(record), metadata

    raw_text = path.read_text(encoding="utf-8")
    if redact_pii:
        redacted = redact_pii_text(raw_text)
        return redacted["text"], {
            "input_type": "plain_text",
            "source_path": str(path),
            "pii_redaction": {
                "enabled": True,
                "summary": summarize_redactions(redacted["redactions"]),
            },
        }
    return raw_text, {"input_type": "plain_text", "source_path": str(path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract transcript/audio/video review cues for the multimodal Signal Engine scaffold."
    )
    parser.add_argument("--text-file", help="Optional transcript text, JSON, or JSONL input.")
    parser.add_argument("--audio-file", help="Optional audio file for bounded feature extraction.")
    parser.add_argument("--video-file", help="Optional video file for bounded feature extraction.")
    parser.add_argument("--out", required=True, help="Path to the output JSON report.")
    parser.add_argument(
        "--domain",
        choices=("support", "sales", "account_management", "earnings"),
        help="Optional domain hint.",
    )
    parser.add_argument(
        "--redact-pii",
        action="store_true",
        help="Apply deterministic PII redaction to transcript text before extraction.",
    )
    parser.add_argument(
        "--use-transformer-emotion",
        action="store_true",
        help="Check whether the optional transformer emotion adapter is available locally.",
    )
    args = parser.parse_args(argv)

    if not any([args.text_file, args.audio_file, args.video_file]):
        raise RuntimeError("At least one of --text-file, --audio-file, or --video-file must be provided.")

    input_metadata: dict[str, Any] = {
        "domain": args.domain,
        "transcript_canonical": True,
        "use_transformer_emotion_requested": args.use_transformer_emotion,
    }

    if args.text_file:
        text, text_metadata = _load_text_input(Path(args.text_file), redact_pii=args.redact_pii)
        input_metadata.update(text_metadata)
        transcript_feature_set = extract_text_feature_set(
            text,
            domain=args.domain,
            source_path=str(args.text_file),
        )
    else:
        transcript_feature_set = extract_text_feature_set("", domain=args.domain)

    audio_feature_set = extract_audio_feature_set(args.audio_file)
    video_feature_set = extract_video_feature_set(args.video_file)

    if args.use_transformer_emotion:
        input_metadata["optional_transformer_emotion"] = {
            "available": optional_transformer_emotion.is_available(),
            "dependency_hint": optional_transformer_emotion.dependency_hint(),
        }

    report = build_multimodal_report(
        input_metadata=input_metadata,
        feature_sets={
            "transcript": transcript_feature_set,
            "audio": audio_feature_set,
            "video": video_feature_set,
        },
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "out": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
