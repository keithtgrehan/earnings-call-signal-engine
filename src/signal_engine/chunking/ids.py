from __future__ import annotations

import hashlib
import re


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").lower() or "unknown"


def stable_object_id(*parts: object, prefix: str) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def stable_chunk_id(case_id: str, chunk_type: str, start_char: int, end_char: int) -> str:
    return stable_object_id(_slug(case_id), chunk_type, start_char, end_char, prefix="chunk")
