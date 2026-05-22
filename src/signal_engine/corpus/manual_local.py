from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import Any


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def parse_transcript_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    lower = text.lower()
    qa_index = lower.find("question-and-answer")
    if qa_index < 0:
        qa_index = lower.find("q&a")
    if qa_index > 0:
        sections.append({"section": "prepared_remarks", "char_start": 0, "char_end": qa_index})
        sections.append({"section": "qa", "char_start": qa_index, "char_end": len(text)})
    else:
        sections.append({"section": "unknown", "char_start": 0, "char_end": len(text)})
    return sections


def speaker_turns(text: str, *, include_preview: bool) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    cursor = 0
    for index, line in enumerate(text.splitlines()):
        start = cursor
        end = cursor + len(line)
        cursor = end + 1
        stripped = line.strip()
        if not stripped:
            continue
        speaker = "unknown"
        body = stripped
        if ":" in stripped:
            speaker, body = stripped.split(":", 1)
            speaker = speaker.strip() or "unknown"
            body = body.strip()
        role = "analyst" if "analyst" in speaker.lower() else "management" if speaker != "unknown" else "unknown"
        turn = {
            "turn_index": len(turns),
            "speaker": speaker,
            "speaker_role": role,
            "char_start": start,
            "char_end": end,
        }
        if include_preview:
            turn["redacted_preview"] = body[:120]
        turns.append(turn)
    return turns


def build_manual_case_record(
    *,
    case_id: str,
    source_path: Path,
    rights_tier: str,
    commit_allowed: bool,
    operator: str,
) -> dict[str, Any]:
    text = source_path.read_text(encoding="utf-8")
    include_preview = commit_allowed is True
    return {
        "case_id": case_id,
        "source_path_ref": str(source_path),
        "source_hash": file_sha256(source_path),
        "rights_tier": rights_tier,
        "commit_allowed": commit_allowed,
        "raw_text_copied": False,
        "registered_at": datetime.now(UTC).isoformat(),
        "operator": operator,
        "sections": parse_transcript_sections(text),
        "speaker_turns": speaker_turns(text, include_preview=include_preview),
        "blocked_reason": "" if commit_allowed else "Raw transcript text not written because commit_allowed is false.",
    }


def validate_manual_case_record(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "case_id",
        "source_path_ref",
        "source_hash",
        "rights_tier",
        "commit_allowed",
        "raw_text_copied",
        "registered_at",
        "operator",
        "sections",
        "speaker_turns",
        "blocked_reason",
    ):
        if field not in row:
            errors.append(f"missing required field {field}")
    if row.get("raw_text_copied") is not False:
        errors.append("manual-local registration must not copy raw text into repo")
    if row.get("commit_allowed") is False:
        for turn in row.get("speaker_turns", []) or []:
            if isinstance(turn, dict) and "redacted_preview" in turn:
                errors.append("redacted previews are not written when commit_allowed is false")
                break
    if not str(row.get("source_hash", "")).startswith("sha256:"):
        errors.append("source_hash must be sha256-prefixed")
    if row.get("rights_tier") in {"unknown", "restricted", ""} and row.get("commit_allowed") is True:
        errors.append("unknown or restricted rights cannot enable committed previews")
    return errors
