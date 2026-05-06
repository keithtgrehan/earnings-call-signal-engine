#!/usr/bin/env python3
"""Intake high-signal earnings-call transcripts with provenance and review scaffolds."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
for path in (SRC, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

USER_AGENT = "SignalEngineTranscriptIntake/1.0 (+public transcript research; no paywalled sources)"
TARGET_TICKERS = (
    "TSLA",
    "AMD",
    "CRM",
    "SNOW",
    "HUBS",
    "NOW",
    "DDOG",
    "NET",
    "MDB",
    "PANW",
    "CRWD",
    "SHOP",
    "UBER",
    "RBLX",
    "COIN",
    "ASML",
    "TSM",
)
MARKERS = (
    "operator",
    "question-and-answer",
    "questions and answers",
    "q&a",
    "prepared remarks",
    "analyst",
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
REMOVE_SELECTORS = (
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "iframe",
    "svg",
    "[class*='advert']",
    "[id*='advert']",
)
MANIFEST_FIELDS = (
    "case_id",
    "ticker",
    "year",
    "quarter",
    "status",
    "source_url",
    "transcript_chars",
    "has_raw",
    "has_processed",
    "has_packet",
    "review_ready",
    "quality_flags",
)


class IntakeError(RuntimeError):
    """Raised for explicit, non-silent intake failures."""


@dataclass(frozen=True)
class SourceCase:
    case_id: str
    ticker: str
    fiscal_year: str
    quarter: str
    source_url: str
    notes: str = ""


@dataclass(frozen=True)
class PlannedCase:
    case_id: str
    ticker: str
    fiscal_year: str
    quarter: str
    source_url: str
    source_type: str
    notes: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean value, got {value!r}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="*", default=list(TARGET_TICKERS))
    parser.add_argument("--ticker-file")
    parser.add_argument("--years", nargs="+", default=["2024", "2025", "2026"])
    parser.add_argument("--quarters", nargs="+", default=["Q1", "Q2", "Q3", "Q4"])
    parser.add_argument("--output-root", default="data/corpus/high_signal_cases")
    parser.add_argument("--max-cases-per-ticker", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", type=parse_bool, nargs="?", const=True, default=False)
    parser.add_argument("--source", default="existing_config", choices=("existing_config", "manual_placeholder"))
    parser.add_argument("--min-transcript-chars", type=int, default=5000)
    parser.add_argument("--require-markers", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=45)
    return parser.parse_args(argv)


def normalize_tickers(args: argparse.Namespace) -> list[str]:
    tickers = [str(ticker).strip().upper() for ticker in (args.tickers or []) if str(ticker).strip()]
    if args.ticker_file:
        path = Path(args.ticker_file)
        file_tickers = [line.strip().upper() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        tickers.extend(file_tickers)
    return list(dict.fromkeys(tickers))


def load_configured_sources(path: Path | None = None) -> dict[str, SourceCase]:
    sources_path = path or (TOOLS / "transcript_downloader" / "sources.yaml")
    if not sources_path.exists():
        return {}
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - only happens when optional dependency is absent.
        raise IntakeError(f"PyYAML is required to read {sources_path}") from exc
    payload = yaml.safe_load(sources_path.read_text(encoding="utf-8")) or {}
    result: dict[str, SourceCase] = {}
    for case_id, raw in (payload.get("cases") or {}).items():
        if not isinstance(raw, dict):
            continue
        result[str(case_id)] = SourceCase(
            case_id=str(case_id),
            ticker=str(raw.get("ticker") or "").upper(),
            fiscal_year=str(raw.get("fiscal_year") or ""),
            quarter=str(raw.get("quarter") or ""),
            source_url=str(raw.get("source_url") or ""),
            notes=str(raw.get("notes") or ""),
        )
    return result


def quarter_sort_key(quarter: str) -> int:
    match = re.search(r"([1-4])", quarter)
    return int(match.group(1)) if match else 0


def plan_cases(
    *,
    tickers: list[str],
    years: list[str],
    quarters: list[str],
    configured_sources: dict[str, SourceCase],
    max_cases_per_ticker: int,
    source_mode: str,
) -> list[PlannedCase]:
    planned: list[PlannedCase] = []
    for ticker in tickers:
        ticker_cases: list[PlannedCase] = []
        for year in years:
            for quarter in quarters:
                case_id = f"{ticker}_{year}_{quarter}"
                configured = configured_sources.get(case_id)
                if source_mode == "existing_config" and configured and configured.source_url:
                    source_url = configured.source_url
                    source_type = guess_source_type(source_url)
                    notes = configured.notes or "Source from tools/transcript_downloader/sources.yaml."
                else:
                    source_url = ""
                    source_type = "manual_placeholder"
                    notes = "No supported public source configured; manual provenance and transcript download required."
                ticker_cases.append(
                    PlannedCase(
                        case_id=case_id,
                        ticker=ticker,
                        fiscal_year=str(year),
                        quarter=str(quarter),
                        source_url=source_url,
                        source_type=source_type,
                        notes=notes,
                    )
                )
        ticker_cases.sort(
            key=lambda item: (
                item.source_type != "manual_placeholder",
                int(item.fiscal_year) if str(item.fiscal_year).isdigit() else 0,
                quarter_sort_key(item.quarter),
            ),
            reverse=True,
        )
        planned.extend(ticker_cases[: max(0, max_cases_per_ticker)])
    return planned


def guess_source_type(url: str) -> str:
    lowered = url.lower().split("?", 1)[0]
    if lowered.endswith(".pdf"):
        return "pdf"
    if url:
        return "html"
    return "manual_placeholder"


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + ("\n" if text.strip() else "")


def robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return False
    return parser.can_fetch(USER_AGENT, url)


def fetch_url(url: str, timeout: int) -> tuple[bytes, str]:
    if not robots_allowed(url):
        raise IntakeError("blocked: robots.txt does not allow this URL")
    try:
        import requests
    except Exception as exc:
        raise IntakeError("requests is required for live transcript downloads") from exc
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*;q=0.8"},
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise IntakeError(f"HTTP error: {response.status_code}")
    return response.content, response.headers.get("content-type", "").lower()


def is_pdf_bytes(url: str, content: bytes, content_type: str) -> bool:
    return url.lower().split("?", 1)[0].endswith(".pdf") or "application/pdf" in content_type or content.startswith(b"%PDF")


def extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise IntakeError("pypdf is required to parse PDF transcripts") from exc
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_html_text(content: bytes, url: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except Exception as exc:
        raise IntakeError("beautifulsoup4 is required to parse HTML transcripts") from exc
    html = content.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for selector in REMOVE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()
    candidates = soup.select("article, main, [class*='transcript'], [id*='transcript']")
    blocks = [node.get_text("\n", strip=True) for node in candidates]
    return max(blocks, key=len) if blocks else soup.get_text("\n", strip=True)


def validate_transcript(text: str, *, min_chars: int, require_markers: bool) -> tuple[str, list[str]]:
    flags: list[str] = []
    lowered = text.lower()
    if len(text) < min_chars:
        flags.append(f"short_transcript:{len(text)}<{min_chars}")
    if any(phrase in lowered for phrase in BLOCK_PHRASES):
        flags.append("blocked_or_paywalled_marker")
    marker_hits = [marker for marker in MARKERS if marker in lowered]
    if require_markers and not marker_hits:
        flags.append("missing_earnings_call_markers")
    elif not marker_hits:
        flags.append("warning_missing_earnings_call_markers")
    has_speaker_structure = bool(re.search(r"(?m)^[A-Z][A-Za-z .,'-]{2,60}:\s+\S", text))
    has_section_markers = any(marker in lowered for marker in ("question-and-answer", "questions and answers", "q&a", "prepared remarks"))
    if not (has_speaker_structure or has_section_markers):
        flags.append("missing_speaker_or_section_structure")
    if any(flag.startswith("short_transcript") or flag in {"blocked_or_paywalled_marker", "missing_earnings_call_markers", "missing_speaker_or_section_structure"} for flag in flags):
        return "failed", flags
    if flags:
        return "warning", flags
    return "valid", []


def parse_transcript(text: str) -> dict[str, Any]:
    lowered = text.lower()
    qa_match = re.search(r"(?i)\b(question-and-answer|questions and answers|q&a)\b", text)
    sections: list[dict[str, Any]] = []
    if qa_match:
        prepared = text[: qa_match.start()].strip()
        qa = text[qa_match.start() :].strip()
        if prepared:
            sections.append({"name": "prepared_remarks", "text": prepared})
        if qa:
            sections.append({"name": "question_and_answer", "text": qa})
    else:
        guessed_name = "prepared_remarks" if "prepared remarks" in lowered else "full_transcript"
        sections.append({"name": guessed_name, "text": text.strip()})
    turns: list[dict[str, Any]] = []
    speaker_re = re.compile(r"(?m)^([A-Z][A-Za-z .,'-]{2,60}):\s*(.+)")
    for section in sections:
        matches = list(speaker_re.finditer(section["text"]))
        if not matches:
            turns.append({"section": section["name"], "speaker": "", "role": "", "text": section["text"][:4000]})
            continue
        for index, match in enumerate(matches):
            start = match.start(2)
            end = matches[index + 1].start() if index + 1 < len(matches) else len(section["text"])
            speaker = match.group(1).strip()
            body = section["text"][start:end].strip()
            role = "analyst" if section["name"] == "question_and_answer" and ("?" in body or "analyst" in speaker.lower()) else ""
            turns.append({"section": section["name"], "speaker": speaker, "role": role, "text": body})
    return {
        "sections": [{"name": row["name"], "char_count": len(row["text"])} for row in sections],
        "speaker_turns": turns,
    }


def weak_label_candidates(case_id: str, parsed: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        from signal_engine.signal_baseline import predict_deterministic_signal_family
    except Exception:
        return []
    candidates: list[dict[str, Any]] = []
    for index, turn in enumerate(parsed.get("speaker_turns") or []):
        text = str(turn.get("text") or "").strip()
        if len(text) < 80:
            continue
        prediction = predict_deterministic_signal_family(text)
        label = str(prediction.get("label") or "neutral")
        confidence = float(prediction.get("confidence") or 0.0)
        if label == "neutral" and confidence <= 0:
            continue
        candidates.append(
            {
                "candidate_id": f"{case_id}_weak_{index:04d}",
                "case_id": case_id,
                "section": turn.get("section", ""),
                "speaker": turn.get("speaker", ""),
                "text": text[:1200],
                "predicted_label": label,
                "confidence": confidence,
                "evidence_terms": prediction.get("evidence_terms") or [],
                "warning": "weak label suggestion only; not gold",
            }
        )
        if len(candidates) >= 40:
            break
    return candidates


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def build_label_packet(case: PlannedCase, provenance: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    lines = [
        f"# Human Labeling Packet: {case.case_id}",
        "",
        "Weak labels are suggestions only. Do not promote any row to gold until a human reviewer accepts it.",
        "",
        "## Case Metadata",
        "",
        f"- ticker: `{case.ticker}`",
        f"- fiscal_year: `{case.fiscal_year}`",
        f"- fiscal_quarter: `{case.quarter}`",
        f"- source_url: `{case.source_url or 'manual_required'}`",
        f"- validation_status: `{provenance['validation_status']}`",
        f"- transcript_char_count: `{provenance['transcript_char_count']}`",
        f"- quality_flags: `{', '.join(provenance['quality_flags']) or 'none'}`",
        "",
        "## Weak-Label Candidates",
        "",
    ]
    if not candidates:
        lines.append("No weak-label candidates were generated. This may mean the transcript is missing, invalid, or only neutral spans were detected.")
    else:
        for item in candidates[:12]:
            terms = ", ".join(str(term) for term in item.get("evidence_terms") or [])
            lines.extend(
                [
                    f"### {item['candidate_id']}",
                    "",
                    f"- suggested_label: `{item['predicted_label']}`",
                    f"- confidence: `{item['confidence']}`",
                    f"- evidence_terms: `{terms or 'none'}`",
                    "",
                    f"> {item['text'][:700]}",
                    "",
                ]
            )
    lines.extend(
        [
            "",
            "## Reviewer Table",
            "",
            "| review_id | evidence_text | reviewer_decision | corrected_label | reviewer_notes |",
            "| --- | --- | --- | --- | --- |",
            "|  |  | accept/reject/unclear | risk_friction/opportunity_commitment/uncertainty_hedging/neutral |  |",
        ]
    )
    return "\n".join(lines) + "\n"


def write_case_outputs(
    *,
    case: PlannedCase,
    output_root: Path,
    overwrite: bool,
    min_chars: int,
    require_markers: bool,
    timeout: int,
) -> dict[str, Any]:
    case_dir = output_root / case.case_id
    raw_dir = case_dir / "raw"
    metadata_dir = case_dir / "metadata"
    processed_dir = case_dir / "processed"
    labels_dir = case_dir / "labels"
    outputs_dir = case_dir / "outputs"
    for directory in (raw_dir, metadata_dir, processed_dir, labels_dir, outputs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    transcript_path = raw_dir / "transcript.txt"
    if transcript_path.exists() and not overwrite:
        raise IntakeError(f"raw transcript already exists and --overwrite is false: {transcript_path}")

    text = ""
    downloaded = False
    quality_flags: list[str] = []
    status = "failed"
    source_type = case.source_type
    raw_source_path = ""
    notes = case.notes
    try:
        if case.source_url:
            content, content_type = fetch_url(case.source_url, timeout)
            if is_pdf_bytes(case.source_url, content, content_type):
                source_type = "pdf"
                raw_source = raw_dir / "transcript.pdf"
                raw_source.write_bytes(content)
                text = extract_pdf_text(content)
            else:
                source_type = "html"
                raw_source = raw_dir / "source.html"
                raw_source.write_bytes(content)
                text = extract_html_text(content, case.source_url)
            text = clean_text(text)
            transcript_path.write_text(text, encoding="utf-8")
            raw_source_path = display_path(raw_source)
            downloaded = True
        else:
            quality_flags.append("manual_transcript_required")
    except Exception as exc:
        quality_flags.append(f"download_or_parse_failed:{exc}")
        notes = f"{notes} Download/parse failure: {exc}".strip()

    if transcript_path.exists():
        text = transcript_path.read_text(encoding="utf-8", errors="replace")
    validation_status, validation_flags = validate_transcript(text, min_chars=min_chars, require_markers=require_markers)
    quality_flags = list(dict.fromkeys([*quality_flags, *validation_flags]))
    if validation_status == "valid":
        status = "valid"
    elif validation_status == "warning":
        status = "warning"

    parsed = parse_transcript(text) if text else {"sections": [], "speaker_turns": []}
    if text:
        (processed_dir / "transcript_clean.txt").write_text(clean_text(text), encoding="utf-8")
        write_json(processed_dir / "transcript_sectioned.json", parsed)
    candidates = weak_label_candidates(case.case_id, parsed) if validation_status in {"valid", "warning"} else []
    write_jsonl(labels_dir / "weak_label_candidates.jsonl", candidates)

    provenance = {
        "case_id": case.case_id,
        "ticker": case.ticker,
        "company_name": "",
        "fiscal_year": case.fiscal_year,
        "fiscal_quarter": case.quarter,
        "source_url": case.source_url,
        "source_type": source_type,
        "downloaded_at": now_iso(),
        "raw_transcript_path": display_path(transcript_path) if transcript_path.exists() else "",
        "transcript_char_count": len(text),
        "validation_status": validation_status,
        "quality_flags": quality_flags,
        "notes": notes,
    }
    write_json(metadata_dir / "provenance.json", provenance)
    (metadata_dir / "source_url.txt").write_text(case.source_url + "\n" if case.source_url else "manual_required\n", encoding="utf-8")
    packet_text = build_label_packet(case, provenance, candidates)
    (labels_dir / "human_labeling_packet.md").write_text(packet_text, encoding="utf-8")
    intake_status = {
        "case_id": case.case_id,
        "status": status,
        "downloaded": downloaded,
        "review_ready": validation_status == "valid",
        "source_type": source_type,
        "source_url": case.source_url,
        "quality_flags": quality_flags,
        "raw_source_path": raw_source_path,
        "message": "No gold labels were created. Human review is required before promotion.",
    }
    write_json(outputs_dir / "intake_status.json", intake_status)
    (outputs_dir / "parse_report.md").write_text(
        "\n".join(
            [
                f"# Parse Report: {case.case_id}",
                "",
                f"- status: `{status}`",
                f"- validation_status: `{validation_status}`",
                f"- transcript_chars: `{len(text)}`",
                f"- sections_detected: `{len(parsed.get('sections') or [])}`",
                f"- speaker_turns_detected: `{len(parsed.get('speaker_turns') or [])}`",
                f"- weak_label_candidates: `{len(candidates)}`",
                f"- quality_flags: `{', '.join(quality_flags) or 'none'}`",
                "",
                "No gold labels were created.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "case_id": case.case_id,
        "ticker": case.ticker,
        "year": case.fiscal_year,
        "quarter": case.quarter,
        "status": status,
        "source_url": case.source_url,
        "transcript_chars": len(text),
        "has_raw": transcript_path.exists(),
        "has_processed": (processed_dir / "transcript_sectioned.json").exists(),
        "has_packet": (labels_dir / "human_labeling_packet.md").exists(),
        "review_ready": validation_status == "valid",
        "quality_flags": ";".join(quality_flags),
    }


def write_manifest(output_root: Path, rows: list[dict[str, Any]]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    with (output_root / "high_signal_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MANIFEST_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in MANIFEST_FIELDS})
    write_json(output_root / "high_signal_manifest.json", rows)


def dry_run_summary(planned: list[PlannedCase], output_root: Path) -> dict[str, Any]:
    configured = [case for case in planned if case.source_url]
    manual = [case for case in planned if not case.source_url]
    return {
        "dry_run": True,
        "tickers_requested": sorted({case.ticker for case in planned}),
        "cases_discovered": len(planned),
        "configured_public_sources": len(configured),
        "manual_placeholders_needed": len(manual),
        "output_root": str(output_root),
        "planned_cases": [case.case_id for case in planned],
        "next_manual_action": "Review labels/human_labeling_packet.md files and promote confirmed rows to gold_labels.jsonl only after human review.",
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tickers = normalize_tickers(args)
    output_root = (ROOT / args.output_root).resolve() if not Path(args.output_root).is_absolute() else Path(args.output_root)
    configured_sources = load_configured_sources()
    planned = plan_cases(
        tickers=tickers,
        years=[str(year) for year in args.years],
        quarters=[str(quarter).upper() for quarter in args.quarters],
        configured_sources=configured_sources,
        max_cases_per_ticker=args.max_cases_per_ticker,
        source_mode=args.source,
    )
    if args.dry_run:
        print(json.dumps(dry_run_summary(planned, output_root), indent=2))
        return 0

    rows: list[dict[str, Any]] = []
    failures = 0
    downloads = 0
    for index, case in enumerate(planned):
        if index and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)
        try:
            row = write_case_outputs(
                case=case,
                output_root=output_root,
                overwrite=args.overwrite,
                min_chars=args.min_transcript_chars,
                require_markers=args.require_markers,
                timeout=args.timeout,
            )
            rows.append(row)
            if row["status"] in {"failed", "warning"}:
                failures += 1
            if row["source_url"] and row["has_raw"]:
                downloads += 1
            print(f"{row['status'].upper()} {case.case_id}: review_ready={row['review_ready']} flags={row['quality_flags']}")
        except Exception as exc:
            failures += 1
            rows.append(
                {
                    "case_id": case.case_id,
                    "ticker": case.ticker,
                    "year": case.fiscal_year,
                    "quarter": case.quarter,
                    "status": "failed",
                    "source_url": case.source_url,
                    "transcript_chars": 0,
                    "has_raw": False,
                    "has_processed": False,
                    "has_packet": False,
                    "review_ready": False,
                    "quality_flags": f"intake_failed:{exc}",
                }
            )
            print(f"FAILED {case.case_id}: {exc}", file=sys.stderr)
    write_manifest(output_root, rows)
    valid = sum(1 for row in rows if row["status"] == "valid")
    review_ready = sum(1 for row in rows if row["review_ready"])
    summary = {
        "tickers_requested": tickers,
        "cases_discovered": len(planned),
        "cases_downloaded": downloads,
        "valid_transcripts": valid,
        "warning_or_failed_transcripts": failures,
        "review_ready_packets_created": review_ready,
        "manifest_path": str(output_root / "high_signal_manifest.csv"),
        "next_manual_action": "Review labels/human_labeling_packet.md files and promote confirmed rows to gold_labels.jsonl only after human review.",
    }
    print(json.dumps(summary, indent=2))
    return 1 if any(str(row.get("quality_flags", "")).startswith("intake_failed") for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
