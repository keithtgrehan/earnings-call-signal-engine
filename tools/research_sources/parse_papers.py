#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "research" / "ilya_reading_list"
DEFAULT_REGISTRY = DATA_DIR / "source_registry.json"
DEFAULT_METADATA = DATA_DIR / "papers_metadata.json"
DEFAULT_EXTRACTED = DATA_DIR / "extracted"

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "because",
    "between",
    "could",
    "from",
    "have",
    "into",
    "more",
    "such",
    "than",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "using",
    "were",
    "which",
    "with",
}


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _read_html(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def _normalize(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _section_excerpt(text: str, heading: str, max_chars: int = 1800) -> str:
    pattern = re.compile(rf"(?im)^\s*(?:\d+\.?\s*)?{re.escape(heading)}\b[:.\s-]*$")
    match = pattern.search(text)
    if not match:
        loose = re.search(rf"(?i)\b{re.escape(heading)}\b", text)
        if not loose:
            return ""
        start = loose.start()
    else:
        start = match.end()
    return text[start : start + max_chars].strip()


def _abstract(text: str) -> str:
    found = _section_excerpt(text, "Abstract", 700)
    if found:
        return found
    return text[:700].strip()


def _sections_detected(text: str) -> list[str]:
    candidates = [
        "Abstract",
        "Introduction",
        "Background",
        "Method",
        "Model",
        "Experiments",
        "Results",
        "Discussion",
        "Conclusion",
        "References",
    ]
    detected = [section for section in candidates if re.search(rf"(?i)\b{re.escape(section)}\b", text)]
    return detected


def _references_sample(text: str) -> list[str]:
    refs = _section_excerpt(text, "References", 3000)
    if not refs:
        return []
    lines = [line.strip() for line in refs.splitlines() if len(line.strip()) > 20]
    return lines[:8]


def _key_terms(text: str, concepts: list[str]) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z-]{4,}", text.lower())
    counts = Counter(word for word in words if word not in STOPWORDS)
    frequent = [word for word, _ in counts.most_common(14)]
    terms = list(dict.fromkeys([*concepts, *frequent]))
    return terms[:18]


def _safe_digest_text(entry: dict[str, Any], extracted: dict[str, Any]) -> str:
    warning = (
        "Full raw source text was parsed locally for analysis when parse_status is full_text_parsed, "
        "but is not committed because redistribution rights for papers, theses, books, and web pages vary by source."
    )
    lines = [
        f"# {entry['title']}",
        "",
        f"Source URL: {extracted['source_url']}",
        f"Extraction status: {extracted['extraction_status']}",
        f"Text length parsed locally: {extracted['text_length_chars']}",
        "",
        warning,
        "",
        "## Detected Sections",
        "",
        *[f"- {section}" for section in extracted["sections_detected"]],
        "",
        "## Abstract / Opening Digest",
        "",
        extracted["abstract"][:500],
        "",
        "## Introduction Digest",
        "",
        extracted["introduction"][:500],
        "",
        "## Conclusion Digest",
        "",
        extracted["conclusion"][:500],
    ]
    return "\n".join(lines).strip() + "\n"


def _add_warning(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse cached Ilya reading-list sources into legal-safe extracted metadata.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--out-dir", default=str(DEFAULT_EXTRACTED))
    args = parser.parse_args()

    registry_path = Path(args.registry)
    entries = json.loads(registry_path.read_text(encoding="utf-8"))
    metadata = {paper["id"]: paper for paper in json.loads(Path(args.metadata).read_text(encoding="utf-8"))}
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        paper = metadata.get(entry["id"], {})
        cache_value = entry.get("local_cache_path")
        warnings = list(entry.get("extraction_warnings", []))
        text = ""
        method = entry.get("extraction_method") or "not_downloaded"

        if cache_value:
            cache_path = ROOT / cache_value
            try:
                if cache_path.suffix.lower() == ".pdf":
                    text = _read_pdf(cache_path)
                    method = "pypdf"
                else:
                    text = _read_html(cache_path)
                    method = "beautifulsoup_html"
            except Exception as exc:  # pragma: no cover - parser/library-specific detail
                _add_warning(warnings, f"Parsing failed: {exc}")
        else:
            _add_warning(warnings, "No local cache file available; committed extraction is citation/abstract-level only.")

        text = _normalize(text)
        if len(text) >= 8000:
            parse_status = "full_text_parsed"
        elif len(text) >= 800:
            parse_status = "abstract_only"
        elif entry.get("source_type") == "citation":
            parse_status = "citation_only"
        else:
            parse_status = entry.get("parse_status") or "source_unavailable"

        extracted = {
            "id": entry["id"],
            "title": entry["title"],
            "authors": entry.get("authors", []),
            "year": entry.get("year"),
            "source_url": entry.get("canonical_url") or entry.get("pdf_url") or entry.get("html_url"),
            "extraction_status": parse_status,
            "extraction_method": method,
            "raw_text_committed": False,
            "text_length_chars": len(text),
            "sections_detected": _sections_detected(text) if text else [],
            "abstract": _abstract(text) if text else paper.get("core_idea", ""),
            "introduction": _section_excerpt(text, "Introduction", 700) if text else "",
            "conclusion": _section_excerpt(text, "Conclusion", 700) if text else "",
            "key_terms": _key_terms(text, paper.get("core_concepts", [])) if text else paper.get("core_concepts", []),
            "references_sample": _references_sample(text),
            "extraction_warnings": warnings
            + ["Raw full text intentionally omitted from git; source cache is ignored and local-only."],
        }

        json_path = out_dir / f"{entry['id']}.json"
        note_path = out_dir / f"{entry['id']}.txt"
        json_path.write_text(json.dumps(extracted, indent=2) + "\n", encoding="utf-8")
        note_path.write_text(_safe_digest_text(entry, extracted), encoding="utf-8")

        entry["parse_status"] = parse_status
        entry["extraction_method"] = method
        entry["committed_text_path"] = None
        entry["committed_note_path"] = str(note_path.relative_to(ROOT))
        entry["extracted_metadata_path"] = str(json_path.relative_to(ROOT))
        entry["extraction_warnings"] = warnings

    registry_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"Parsed {len(entries)} sources into {out_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
