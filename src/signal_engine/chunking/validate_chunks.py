from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .schemas import CHUNK_TYPES

SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def validate_chunk_manifest_rows(rows: list[dict[str, Any]], *, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        prefix = f"row {index} {row.get('chunk_id', '')}: "
        if row.get("chunk_type") not in CHUNK_TYPES and row.get("chunk_type") not in {"transcript_text", "audio_asr_text", "metadata_only"}:
            errors.append(prefix + "invalid chunk_type")
        if row.get("raw_text_committed") != "false":
            errors.append(prefix + "raw_text_committed must be false")
        for field in ("source_sha256", "text_sha256"):
            if not SHA_RE.match(str(row.get(field, ""))):
                errors.append(prefix + f"{field} must be sha256")
        if repo_root and row.get("local_chunk_path"):
            try:
                Path(str(row["local_chunk_path"])).resolve().relative_to(repo_root.resolve())
                errors.append(prefix + "local_chunk_path must not be inside git repo")
            except (OSError, ValueError):
                pass
    return errors
