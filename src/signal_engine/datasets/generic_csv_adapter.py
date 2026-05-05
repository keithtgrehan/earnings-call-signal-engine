from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_generic_csv(path: str | Path, *, text_column: str = "text", label_column: str = "label") -> list[dict[str, Any]]:
    """Load a local CSV into a benchmark-only text/label shape."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file does not exist locally: {csv_path}")
    rows: list[dict[str, Any]] = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if text_column not in (reader.fieldnames or []) or label_column not in (reader.fieldnames or []):
            raise ValueError(f"CSV must include `{text_column}` and `{label_column}` columns.")
        for row in reader:
            text = str(row.get(text_column) or "").strip()
            label = str(row.get(label_column) or "").strip()
            if text and label:
                rows.append({"text": text, "external_label": label, "source_path": str(csv_path)})
    return rows
