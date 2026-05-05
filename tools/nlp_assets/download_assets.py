#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "nlp_assets"
REGISTRY_JSON = DATA_DIR / "asset_registry.json"
REGISTRY_CSV = DATA_DIR / "asset_registry.csv"
CACHE_DIR = DATA_DIR / "cache"
FIELDNAMES = [
    "id",
    "name",
    "category",
    "source_url",
    "license",
    "download_allowed",
    "download_status",
    "local_path",
    "committed",
    "intended_use",
    "signal_engine_relevance",
    "limitations",
    "priority",
]


def _download(url: str, path: Path) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KeithGrehanSignalEngine/1.0 keithtgrehan@example.com",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        content = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            content = gzip.decompress(content)
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _write_csv(entries: list[dict[str, Any]]) -> None:
    with REGISTRY_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    key: json.dumps(entry[key]) if isinstance(entry.get(key), list) else entry.get(key, "")
                    for key in FIELDNAMES
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely cache small public NLP asset metadata/reference files.")
    parser.add_argument("--safe-only", action="store_true", help="Download only entries with explicit safe_download_url.")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entries = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    for entry in entries:
        url = entry.get("safe_download_url")
        if args.safe_only and not url:
            continue
        if not url or entry.get("download_allowed") is not True:
            continue
        cache_path = CACHE_DIR / entry.get("cache_filename", f"{entry['id']}.txt")
        try:
            sha256 = _download(url, cache_path)
        except Exception as exc:  # pragma: no cover - network-specific
            entry["download_status"] = "unavailable"
            warning = f"Safe download failed: {exc}"
            if warning not in entry["limitations"]:
                entry["limitations"].append(warning)
            continue
        entry["download_status"] = "downloaded"
        entry["local_path"] = str(cache_path.relative_to(ROOT))
        entry["committed"] = False
        entry["sha256"] = sha256
        entry["limitations"] = [item for item in entry["limitations"] if not item.startswith("Safe download failed:")]

    REGISTRY_JSON.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    _write_csv(entries)
    print("Safe NLP asset download pass complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
