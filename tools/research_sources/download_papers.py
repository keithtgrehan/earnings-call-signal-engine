#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "data" / "research" / "ilya_reading_list" / "source_registry.json"
DEFAULT_CACHE = ROOT / "data" / "research" / "ilya_reading_list" / "cache"


def _extension(url: str, source_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".pdf", ".html", ".htm", ".txt"}:
        return suffix
    if source_type == "pdf":
        return ".pdf"
    return ".html"


def _download(url: str, path: Path) -> str:
    response = requests.get(url, timeout=45, headers={"User-Agent": "SignalEngineResearchAsset/1.0"})
    response.raise_for_status()
    path.write_bytes(response.content)
    return hashlib.sha256(response.content).hexdigest()


def _add_warning(entry: dict, warning: str) -> None:
    entry["extraction_warnings"] = entry.get("extraction_warnings", [])
    if warning not in entry["extraction_warnings"]:
        entry["extraction_warnings"].append(warning)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download legally public research sources into an ignored local cache.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Path to source_registry.json.")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE), help="Ignored local cache directory.")
    parser.add_argument("--force", action="store_true", help="Re-download even if a local cache file exists.")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    entries = json.loads(registry_path.read_text(encoding="utf-8"))
    for entry in entries:
        url = entry.get("pdf_url") or entry.get("html_url") or entry.get("canonical_url")
        allowed = entry.get("download_allowed")
        if not url or allowed is not True:
            _add_warning(entry, "Download skipped: download_allowed is not true.")
            continue

        source_type = entry.get("source_type", "html")
        cache_path = cache_dir / f"{entry['id']}{_extension(url, source_type)}"
        if cache_path.exists() and not args.force:
            digest = hashlib.sha256(cache_path.read_bytes()).hexdigest()
        else:
            try:
                digest = _download(url, cache_path)
            except Exception as exc:  # pragma: no cover - network-specific detail
                entry["parse_status"] = "source_unavailable"
                entry["extraction_method"] = "download_failed"
                _add_warning(entry, f"Download failed: {exc}")
                continue

        entry["sha256"] = digest
        entry["local_cache_path"] = str(cache_path.relative_to(ROOT))
        entry["extraction_method"] = "downloaded_pdf" if cache_path.suffix.lower() == ".pdf" else "downloaded_html"

    registry_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {registry_path} with local cache paths and hashes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
