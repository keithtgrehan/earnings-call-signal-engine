from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .objects import validate_retrieval_object


def serialize_retrieval_objects(objects: list[dict[str, Any]], *, out_path: Path | None = None) -> str:
    errors: list[str] = []
    for index, row in enumerate(objects, start=1):
        for error in validate_retrieval_object(row):
            errors.append(f"row {index}: {error}")
    if errors:
        raise ValueError("; ".join(errors))
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in objects) + ("\n" if objects else "")
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
    return payload
