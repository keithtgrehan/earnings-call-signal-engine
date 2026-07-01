from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .index_local import score_query


def load_index(path: Path) -> dict[str, Any]:
    index_path = path / "index.json" if path.is_dir() else path
    if not index_path.exists():
        return {"documents": [], "document_count": 0}
    return json.loads(index_path.read_text(encoding="utf-8"))


def query_local_index(index_path: Path, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    return score_query(load_index(index_path), query, limit=limit)
