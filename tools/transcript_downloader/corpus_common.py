#!/usr/bin/env python3
"""Shared helpers for the local earnings-call transcript corpus."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

APPROVED_REPO = Path("/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa")
APPROVED_BRANCH_BASE = "signal-engine-2.0"
APPROVED_BRANCH_PREFIX = "codex/transcript-corpus-pipeline"
APPROVED_GOLD_LABEL_CYCLE_PREFIX = "codex/"
APPROVED_GOLD_LABEL_CYCLE_SUFFIX = "-gold-label-cycle"
APPROVED_ORIGIN_SUFFIX = "keithtgrehan/earnings-call-signal-engine.git"
APPROVED_CORPUS_ROOT = Path("/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts")
EXPECTED_ACTIVE_CASES = 31

# The intentionally excluded case is kept opaque in generated reports/docs.
EXCLUDED_CASE_ID = "COST_2025_Q4"
EXCLUDED_TICKER = "COST"
EXCLUDED_TERMS = (EXCLUDED_CASE_ID, EXCLUDED_TICKER)

CASE_ID_RE = re.compile(r"^[A-Z]+_[0-9]{4}_Q[1-4]$")
MARKERS = (
    "operator",
    "question-and-answer",
    "questions and answers",
    "q&a",
    "analyst",
    "prepared remarks",
    "conference call",
    "earnings call",
)
BLOCK_PHRASES = (
    "access denied",
    "are you a robot",
    "captcha",
    "forbidden",
    "login required",
    "paywall",
    "please log in",
    "please sign in",
    "subscribe to continue",
    "subscription required",
    "temporarily blocked",
)
BOILERPLATE_PATTERNS = (
    r"^\s*advertisement\s*$",
    r"^\s*related articles\s*$",
    r"^\s*recommended stories\s*$",
    r"^\s*read more\s*$",
    r"^\s*copyright .* rights reserved\s*$",
)

SECTOR_BY_TICKER = {
    "AAPL": "tech",
    "ADBE": "tech",
    "AMZN": "retail",
    "BAC": "banking",
    "BA": "industrials",
    "CAT": "industrials",
    "CRM": "tech",
    "DE": "industrials",
    "DIS": "media",
    "FDX": "logistics",
    "GOOGL": "tech",
    "HD": "retail",
    "INTC": "semiconductors",
    "JNJ": "pharma",
    "JPM": "banking",
    "LLY": "pharma",
    "META": "tech",
    "MSFT": "tech",
    "NKE": "retail",
    "NOW": "tech",
    "NVDA": "semiconductors",
    "ORCL": "tech",
    "PFE": "pharma",
    "PYPL": "payments",
    "SBUX": "retail",
    "SNOW": "tech",
    "TGT": "retail",
    "TSLA": "retail",
    "UPS": "logistics",
    "WMT": "retail",
}


@dataclass(frozen=True)
class CaseInfo:
    case_id: str
    ticker: str
    fiscal_year: int
    quarter: str
    source_url: str
    notes: str = ""

    @property
    def sector(self) -> str:
        return SECTOR_BY_TICKER.get(self.ticker, "tech")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_git(args: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd or repo_root()), text=True).strip()


def is_approved_tool_branch(branch: str) -> bool:
    return (
        branch == APPROVED_BRANCH_BASE
        or branch.startswith(APPROVED_BRANCH_PREFIX)
        or (
            branch.startswith(APPROVED_GOLD_LABEL_CYCLE_PREFIX)
            and branch.endswith(APPROVED_GOLD_LABEL_CYCLE_SUFFIX)
        )
    )


def enforce_repo_safety(*, require_base_branch: bool = False) -> None:
    root = repo_root().resolve()
    if root != APPROVED_REPO:
        raise SystemExit(f"Safety stop: repo path mismatch: {root}")
    branch = run_git(["branch", "--show-current"], root)
    if require_base_branch and branch != APPROVED_BRANCH_BASE:
        raise SystemExit(f"Safety stop: branch must be {APPROVED_BRANCH_BASE}, got {branch}")
    if not is_approved_tool_branch(branch):
        raise SystemExit(f"Safety stop: unexpected branch {branch}")
    origin = run_git(["remote", "get-url", "origin"], root)
    if not origin.endswith(APPROVED_ORIGIN_SUFFIX):
        raise SystemExit(f"Safety stop: origin mismatch: {origin}")
    if not APPROVED_CORPUS_ROOT.exists() or not APPROVED_CORPUS_ROOT.is_dir():
        raise SystemExit(f"Safety stop: corpus root missing: {APPROVED_CORPUS_ROOT}")


def enforce_exact_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if resolved != APPROVED_CORPUS_ROOT:
        raise SystemExit(f"Safety stop: corpus root mismatch: {resolved}")
    return resolved


def sources_path() -> Path:
    return Path(__file__).with_name("sources.yaml")


def load_sources(path: Path | None = None) -> dict[str, CaseInfo]:
    payload = yaml.safe_load((path or sources_path()).read_text(encoding="utf-8")) or {}
    cases = payload.get("cases") or {}
    result: dict[str, CaseInfo] = {}
    for case_id, raw in cases.items():
        if case_id == EXCLUDED_CASE_ID:
            continue
        result[case_id] = CaseInfo(
            case_id=case_id,
            ticker=str(raw["ticker"]),
            fiscal_year=int(raw["fiscal_year"]),
            quarter=str(raw["quarter"]),
            source_url=str(raw.get("source_url", "")),
            notes=str(raw.get("notes", "")),
        )
    return result


def active_case_dirs(root: Path) -> list[Path]:
    dirs = [
        item
        for item in root.iterdir()
        if item.is_dir() and CASE_ID_RE.match(item.name) and item.name != EXCLUDED_CASE_ID
    ]
    return sorted(dirs, key=lambda item: item.name)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def backup_corpus(root: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = root.parent / f"{root.name}_backup_{stamp}"
    if backup.exists():
        raise SystemExit(f"Safety stop: backup path already exists: {backup}")
    shutil.copytree(root, backup)
    return backup


def remove_excluded_case(root: Path) -> None:
    excluded = root / EXCLUDED_CASE_ID
    if excluded.exists():
        shutil.rmtree(excluded)


def scrub_excluded_references(root: Path) -> None:
    for path in root.glob("*.csv"):
        if path.name in {"raw_hash_manifest_before.csv", "raw_hash_manifest_after.csv"}:
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        kept = [line for line in lines if not any(term in line for term in EXCLUDED_TERMS)]
        path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def raw_hash_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_dir in active_case_dirs(root):
        transcript = case_dir / "raw" / "transcript.txt"
        if transcript.exists():
            rows.append({"case_id": case_dir.name, "path": str(transcript), "sha256": sha256_file(transcript)})
    return rows


def compare_hash_rows(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[str]:
    before_map = {str(row["case_id"]): str(row["sha256"]) for row in before}
    after_map = {str(row["case_id"]): str(row["sha256"]) for row in after}
    problems: list[str] = []
    for case_id, before_hash in before_map.items():
        if case_id not in after_map:
            problems.append(f"{case_id}: raw transcript missing after run")
        elif after_map[case_id] != before_hash:
            problems.append(f"{case_id}: raw transcript hash changed")
    for case_id in sorted(set(after_map) - set(before_map)):
        problems.append(f"{case_id}: new raw transcript appeared after pre-run hash")
    return problems


def clean_transcript(text: str) -> tuple[str, dict[str, Any]]:
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    encoding_fixes = text.count("\ufffd")
    text = text.replace("\ufffd", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    cleaned: list[str] = []
    duplicate_lines = 0
    boilerplate = 0
    previous = ""
    seen_nav: dict[str, int] = {}
    for line in lines:
        if not line:
            if cleaned and cleaned[-1]:
                cleaned.append("")
            continue
        lowered = line.lower()
        if any(re.search(pattern, lowered) for pattern in BOILERPLATE_PATTERNS):
            boilerplate += 1
            continue
        seen_nav[lowered] = seen_nav.get(lowered, 0) + 1
        if seen_nav[lowered] > 4 and len(line) < 120:
            boilerplate += 1
            continue
        if line == previous:
            duplicate_lines += 1
            continue
        cleaned.append(line)
        previous = line
    result = "\n".join(cleaned).strip() + "\n"
    report = {
        "encoding_fixes": encoding_fixes,
        "duplicate_lines_removed": duplicate_lines,
        "removed_boilerplate_count": boilerplate,
        "whitespace_normalization": True,
        "repeated_navigation_footer_ad_text": boilerplate,
        "raw_char_count": len(text),
        "clean_char_count": len(result),
    }
    return result, report


def split_sections(text: str) -> dict[str, str]:
    q_match = re.search(
        r"(?im)^\s*(question-and-answer|questions and answers|questions & answers|q&a|q and a|question and answer|question & answer)\b.*$",
        text,
    )
    if q_match:
        prepared = text[: q_match.start()].strip()
        qa = text[q_match.start() :].strip()
        return {"prepared_remarks": prepared, "q_and_a": qa, "unknown": ""}
    transition = re.search(
        r"(?i)(open (?:the )?(?:call )?(?:up )?(?:for|to) questions|"
        r"open for questions|"
        r"operator,? (?:please )?(?:poll for|open|may we have|get|could we get) (?:the )?(?:first |next )?question|"
        r"(?:head over|move on) to (?:investor|analyst) questions|"
        r"(?:first|next) (?:analyst )?question (?:is|comes|will be|from)|"
        r"we will now (?:be )?(?:taking|take) (?:a )?question)",
        text,
    )
    if transition:
        return {"prepared_remarks": text[: transition.start()].strip(), "q_and_a": text[transition.start() :].strip(), "unknown": ""}
    op_matches = list(re.finditer(r"(?im)^\s*operator\s*$", text))
    if len(op_matches) >= 2:
        second = op_matches[1].start()
        return {"prepared_remarks": text[:second].strip(), "q_and_a": text[second:].strip(), "unknown": ""}
    return {"prepared_remarks": "", "q_and_a": "", "unknown": text.strip()}


def speaker_turns(text: str, sections: dict[str, str]) -> list[dict[str, Any]]:
    section_ranges: list[tuple[str, int, int]] = []
    cursor = 0
    for name in ("prepared_remarks", "q_and_a", "unknown"):
        part = sections.get(name, "")
        if not part:
            continue
        start = text.find(part, cursor)
        if start < 0:
            start = cursor
        end = start + len(part)
        section_ranges.append((name, start, end))
        cursor = end
    heading = re.compile(r"(?m)^(?P<speaker>[A-Z][A-Za-z .,'&/-]{1,80})(?:\s+-\s*(?P<role>[^:\n]{1,80}))?\s*$")
    matches = [m for m in heading.finditer(text) if not _is_false_speaker(m.group("speaker"))]
    turns: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if len(body) < 20:
            continue
        speaker = re.sub(r"\s+", " ", match.group("speaker")).strip()
        raw_role = (match.group("role") or "").lower()
        section = _section_for_span(section_ranges, start)
        role = classify_role(speaker, raw_role, body, section)
        turns.append(
            {
                "speaker": speaker,
                "role": role,
                "section": section,
                "text": body,
                "char_start": int(start),
                "char_end": int(end),
            }
        )
    if not turns:
        turns.append({"speaker": "Unknown", "role": "unknown", "section": "unknown", "text": text.strip(), "char_start": 0, "char_end": len(text)})
    return turns


def _is_false_speaker(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in {
        "prepared remarks",
        "question-and-answer session",
        "question and answer session",
        "questions and answers",
        "corporate participants",
        "conference call participants",
        "presentation",
    }


def _section_for_span(ranges: list[tuple[str, int, int]], pos: int) -> str:
    for name, start, end in ranges:
        if start <= pos <= end:
            return name
    return "unknown"


def classify_role(speaker: str, raw_role: str, text: str, section: str) -> str:
    lowered = f"{speaker} {raw_role}".lower()
    if "operator" in lowered:
        return "operator"
    if any(term in lowered for term in ("analyst", "securities", "capital", "bank", "morgan", "goldman", "ubs", "j.p.", "rbc", "barclays")):
        return "analyst"
    if section == "q_and_a" and "?" in text[:500]:
        return "analyst"
    if any(term in lowered for term in ("ceo", "cfo", "president", "chief", "officer", "founder", "chair")):
        return "executive"
    if section == "prepared_remarks":
        return "executive"
    return "unknown"


def contains_block_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in BLOCK_PHRASES)


def marker_flags(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        "contains_operator": "operator" in lowered,
        "contains_q_and_a": any(marker in lowered for marker in ("question-and-answer", "questions and answers", "q&a", "question and answer")),
        "contains_safe_harbor": any(marker in lowered for marker in ("safe harbor", "forward-looking", "actual results may differ")),
        "contains_any_earnings_marker": any(marker in lowered for marker in MARKERS),
    }


def source_type_for(case_dir: Path, info: CaseInfo | None = None) -> str:
    if (case_dir / "raw" / "transcript.pdf").exists():
        return "pdf"
    url = info.source_url if info else ""
    if url.lower().endswith(".pdf"):
        return "pdf"
    return "html"


def active_reference_grep(root: Path) -> dict[str, Any]:
    paths: list[Path] = []
    for base in (root, repo_root() / "tools" / "transcript_downloader"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".csv", ".json", ".jsonl", ".yaml", ".yml", ".txt", ".py"}:
                if "backup" in path.parts:
                    continue
                paths.append(path)
    hits: list[str] = []
    for path in paths:
        if path.name == "corpus_common.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for term in EXCLUDED_TERMS:
            if term in text:
                hits.append(str(path))
                break
    return {"passed": not hits, "hits": sorted(set(hits))}
