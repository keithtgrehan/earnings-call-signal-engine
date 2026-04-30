#!/usr/bin/env python3
"""Normalize, audit-gate, and analyze the local transcript corpus."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_common import (  # noqa: E402
    EXPECTED_ACTIVE_CASES,
    active_case_dirs,
    active_reference_grep,
    backup_corpus,
    clean_transcript,
    compare_hash_rows,
    enforce_exact_root,
    enforce_repo_safety,
    load_sources,
    marker_flags,
    now_iso,
    raw_hash_rows,
    read_text,
    remove_excluded_case,
    repo_root,
    scrub_excluded_references,
    sha256_file,
    source_type_for,
    speaker_turns,
    split_sections,
    write_csv,
    write_json,
    write_jsonl,
)

SRC = repo_root() / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from earnings_call_sentiment.signals.rule_tables import REASSURANCE_RULES, SKEPTICISM_RULES, UNCERTAINTY_RULES
except Exception:  # pragma: no cover - defensive fallback for standalone use.
    REASSURANCE_RULES = ()
    SKEPTICISM_RULES = ()
    UNCERTAINTY_RULES = ()


SIGNAL_TYPES = {
    "guidance_revision",
    "uncertainty",
    "analyst_pressure",
    "commitment",
    "neutral",
    "tone_shift",
    "risk_friction",
    "opportunity_commitment",
}

GUIDANCE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("up", "raised_guidance", r"\b(raise|raises|raised|raising|increase|increased|increasing)\b.{0,80}\b(guidance|outlook|forecast|revenue|eps)\b"),
    ("up", "guidance_raised_reverse", r"\b(guidance|outlook|forecast|revenue|eps)\b.{0,80}\b(raise|raised|higher|above|up from|increase|increased)\b"),
    ("down", "lowered_guidance", r"\b(lower|lowered|lowering|reduce|reduced|cut|down)\b.{0,80}\b(guidance|outlook|forecast|revenue|eps)\b"),
    ("down", "guidance_lowered_reverse", r"\b(guidance|outlook|forecast|revenue|eps)\b.{0,80}\b(lower|lowered|reduced|cut|down)\b"),
    ("unchanged", "reaffirmed_guidance", r"\b(reaffirm|reaffirmed|maintain|maintained|reiterate|reiterated)\b.{0,80}\b(guidance|outlook|forecast)\b"),
)
COMMITMENT_PATTERNS = (
    r"\bcommitted to\b",
    r"\bwe will continue\b",
    r"\bwe remain confident\b",
    r"\bwell positioned\b",
    r"\bon track\b",
)
RISK_PATTERNS = (
    r"\bmargin pressure\b",
    r"\bdemand softness\b",
    r"\bweakness\b",
    r"\brisk\b",
    r"\bheadwind\b",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    return parser.parse_args()


def load_audit(root: Path) -> dict[str, dict[str, str]]:
    path = root / "transcript_quality_audit.csv"
    if not path.exists():
        raise SystemExit("Audit file missing. Run audit_transcripts.py first.")
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["case_id"]: row for row in csv.DictReader(handle)}


def boolish(value: Any) -> bool:
    return str(value).lower() in {"true", "1", "yes"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sentence_spans(text: str) -> list[tuple[str, int, int]]:
    spans: list[tuple[str, int, int]] = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]+|$)", text):
        sentence = match.group(0).strip()
        if len(sentence) < 20:
            continue
        start = text.find(sentence, match.start(), match.end())
        spans.append((sentence, start, start + len(sentence)))
    return spans


def signal_payload(case_id: str, signal_type: str, confidence: float, evidence: str, start: int, end: int, section: str, speaker: str, direction: str) -> dict[str, Any]:
    return {
        "type": signal_type,
        "confidence": round(float(confidence), 3),
        "evidence_text": evidence,
        "start_char": int(start),
        "end_char": int(end),
        "section": section,
        "speaker": speaker,
        "direction": direction,
    }


def extract_guidance(case_id: str, text: str) -> list[dict[str, Any]]:
    guidance: list[dict[str, Any]] = []
    for sentence, start, end in sentence_spans(text):
        lowered = sentence.lower()
        for direction, rule_name, pattern in GUIDANCE_PATTERNS:
            if re.search(pattern, lowered):
                guidance.append(
                    {
                        "metric": infer_metric(sentence),
                        "previous": "",
                        "current": sentence,
                        "direction": direction,
                        "confidence": 0.72 if direction != "unknown" else 0.45,
                        "evidence_text": sentence,
                        "start_char": start,
                        "end_char": end,
                        "source_rule": rule_name,
                    }
                )
                break
        if len(guidance) >= 20:
            break
    return guidance


def infer_metric(sentence: str) -> str:
    lowered = sentence.lower()
    for metric in ("revenue", "eps", "margin", "operating income", "capex", "free cash flow", "guidance", "outlook"):
        if metric in lowered:
            return metric
    return "guidance"


def extract_signals(case_id: str, text: str, turns: list[dict[str, Any]], guidance: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for item in guidance[:8]:
        direction = {"up": "positive", "down": "negative", "unchanged": "neutral"}.get(str(item["direction"]), "unknown")
        speaker = speaker_for_span(turns, int(item["start_char"]))
        section = section_for_span(turns, int(item["start_char"]))
        signals.append(signal_payload(case_id, "guidance_revision", item["confidence"], item["evidence_text"], item["start_char"], item["end_char"], section, speaker, direction))

    for turn in turns:
        for sentence, rel_start, rel_end in sentence_spans(str(turn["text"])):
            start = int(turn["char_start"]) + rel_start
            end = int(turn["char_start"]) + rel_end
            lowered = sentence.lower()
            if turn["role"] == "analyst":
                for rule in SKEPTICISM_RULES:
                    if re.search(str(rule["pattern"]), lowered):
                        signals.append(signal_payload(case_id, "analyst_pressure", min(0.85, 0.45 + int(rule["strength"]) / 10), sentence, start, end, str(turn["section"]), str(turn["speaker"]), "negative"))
                        break
            if turn["role"] in {"executive", "unknown"}:
                for rule in UNCERTAINTY_RULES:
                    if re.search(str(rule["pattern"]), lowered):
                        signals.append(signal_payload(case_id, "uncertainty", min(0.85, 0.40 + int(rule["strength"]) / 10), sentence, start, end, str(turn["section"]), str(turn["speaker"]), "negative"))
                        break
                if any(re.search(pattern, lowered) for pattern in COMMITMENT_PATTERNS):
                    signals.append(signal_payload(case_id, "commitment", 0.66, sentence, start, end, str(turn["section"]), str(turn["speaker"]), "positive"))
                elif any(re.search(pattern, lowered) for pattern in RISK_PATTERNS):
                    signals.append(signal_payload(case_id, "risk_friction", 0.58, sentence, start, end, str(turn["section"]), str(turn["speaker"]), "negative"))
                else:
                    for rule in REASSURANCE_RULES:
                        if re.search(str(rule["pattern"]), lowered):
                            signals.append(signal_payload(case_id, "opportunity_commitment", min(0.82, 0.45 + int(rule["strength"]) / 10), sentence, start, end, str(turn["section"]), str(turn["speaker"]), "positive"))
                            break
        if len(signals) >= 80:
            break

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for signal in sorted(signals, key=lambda row: (-float(row["confidence"]), int(row["start_char"]))):
        key = (str(signal["type"]), int(signal["start_char"]), int(signal["end_char"]))
        if key not in seen:
            seen.add(key)
            deduped.append(signal)
    if not deduped:
        first = next(iter(sentence_spans(text)), (text[:250].strip(), 0, min(len(text), 250)))
        deduped.append(signal_payload(case_id, "neutral", 0.25, first[0], first[1], first[2], "unknown", "Unknown", "neutral"))
    return deduped[:50]


def speaker_for_span(turns: list[dict[str, Any]], pos: int) -> str:
    for turn in turns:
        if int(turn["char_start"]) <= pos <= int(turn["char_end"]):
            return str(turn["speaker"])
    return "Unknown"


def section_for_span(turns: list[dict[str, Any]], pos: int) -> str:
    for turn in turns:
        if int(turn["char_start"]) <= pos <= int(turn["char_end"]):
            return str(turn["section"])
    return "unknown"


def validate_signals(case_id: str, payload: dict[str, Any], text_len: int) -> list[str]:
    errors: list[str] = []
    if payload.get("case_id") != case_id:
        errors.append("missing or mismatched case_id")
    signals = payload.get("signals")
    if not isinstance(signals, list):
        return [*errors, "signals missing"]
    for index, signal in enumerate(signals):
        if signal.get("type") not in SIGNAL_TYPES:
            errors.append(f"signal {index}: invalid type")
        if not str(signal.get("evidence_text") or "").strip():
            errors.append(f"signal {index}: missing evidence_text")
        if not isinstance(signal.get("confidence"), (int, float)):
            errors.append(f"signal {index}: confidence not numeric")
        start = signal.get("start_char")
        end = signal.get("end_char")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start or end > text_len:
            errors.append(f"signal {index}: invalid char span")
    return errors


def write_case_metadata(case_dir: Path, info: Any, source_type: str, transcript: Path, pdf: Path | None) -> None:
    text = read_text(transcript)
    write_json(
        case_dir / "metadata.json",
        {
            "case_id": info.case_id,
            "ticker": info.ticker,
            "fiscal_year": info.fiscal_year,
            "quarter": info.quarter,
            "source_url": info.source_url,
            "source_type": source_type,
            "download_status": "success",
            "downloaded_at": "",
            "sha256": sha256_file(transcript),
            "char_count": len(text),
            "file_paths": {"transcript_txt": str(transcript), "transcript_pdf": str(pdf) if pdf and pdf.exists() else ""},
            "sector": info.sector,
            "notes": info.notes,
        },
    )


def write_gold_scaffold(case_dir: Path, case_id: str) -> bool:
    selected = {"NVDA_2026_Q4", "META_2025_Q4", "AMZN_2025_Q4", "MSFT_2026_Q1", "AAPL_2026_Q1"}
    if case_id not in selected:
        return False
    guide = case_dir / "labels" / "gold_labeling_instructions.md"
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(
        "\n".join(
            [
                "# Gold Labeling Starter",
                "",
                "Add 5-10 human-reviewed JSONL rows to `gold_labels.jsonl`.",
                "Use exact transcript character spans and do not add unsupported claims.",
                "",
                "Required JSONL keys: type, text_span, start_char, end_char, reviewer, rationale.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    gold_path = case_dir / "labels" / "gold_labels.jsonl"
    if not gold_path.exists():
        gold_path.write_text("", encoding="utf-8")
    return True


def weak_labels_from_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    allowed = {"guidance_revision", "uncertainty", "analyst_pressure", "commitment", "neutral"}
    for signal in signals:
        label_type = str(signal["type"])
        if label_type not in allowed:
            label_type = "commitment" if label_type == "opportunity_commitment" else "uncertainty"
        labels.append(
            {
                "type": label_type,
                "text_span": signal["evidence_text"],
                "start_char": signal["start_char"],
                "end_char": signal["end_char"],
                "source_rule": "deterministic_transcript_rule",
                "confidence": min(float(signal["confidence"]), 0.75),
            }
        )
    return labels


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def valid_label_rows(path: Path, *, require_human_label: bool) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    for row in load_jsonl(path):
        if not {"type", "text_span", "start_char", "end_char"}.issubset(row):
            continue
        if require_human_label and row.get("human_label") is not True:
            continue
        if not isinstance(row.get("start_char"), int) or not isinstance(row.get("end_char"), int):
            continue
        if int(row["start_char"]) < 0 or int(row["end_char"]) <= int(row["start_char"]):
            continue
        if not str(row.get("text_span", "")).strip():
            continue
        labels.append(row)
    return labels


def valid_gold_labels(path: Path) -> list[dict[str, Any]]:
    """Return final benchmark labels only.

    Final evaluation intentionally requires explicit human_label=true metadata
    so assistant-reviewed draft rows cannot become benchmark truth by accident.
    """

    return valid_label_rows(path, require_human_label=True)


def spans_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def evaluate_case_labels(
    case_dir: Path,
    *,
    label_filename: str = "gold_labels.jsonl",
    require_human_label: bool = True,
    label_count_field: str = "gold_label_count",
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    gold_rows = valid_label_rows(case_dir / "labels" / label_filename, require_human_label=require_human_label)
    if not gold_rows:
        return None, []
    weak_rows = load_jsonl(case_dir / "labels" / "weak_labels.jsonl")
    matched_weak: set[int] = set()
    matched_count = 0
    type_match_count = 0
    type_mismatch_count = 0
    overlap_match_count = 0
    exact_match_count = 0
    missed_gold_count = 0
    error_rows: list[dict[str, Any]] = []

    for gold in gold_rows:
        g_start = int(gold["start_char"])
        g_end = int(gold["end_char"])
        best_index: int | None = None
        best_overlap = 0
        best_row: dict[str, Any] | None = None
        for index, weak in enumerate(weak_rows):
            if index in matched_weak:
                continue
            try:
                w_start = int(weak.get("start_char"))
                w_end = int(weak.get("end_char"))
            except (TypeError, ValueError):
                continue
            overlap = spans_overlap(g_start, g_end, w_start, w_end)
            if overlap > best_overlap:
                best_index = index
                best_overlap = overlap
                best_row = weak
        if best_row is None or best_index is None or best_overlap <= 0:
            missed_gold_count += 1
            error_rows.append(
                {
                    "case_id": case_dir.name,
                    "error_type": "missed_signal",
                    "gold_type": gold.get("type", ""),
                    "weak_type": "",
                    "evidence_text": gold.get("text_span", ""),
                    "notes": "Gold label had no overlapping weak-label span.",
                }
            )
            continue
        matched_weak.add(best_index)
        matched_count += 1
        same_type = str(best_row.get("type")) == str(gold.get("type"))
        exactish = same_type and abs(int(best_row.get("start_char")) - g_start) <= 5 and abs(int(best_row.get("end_char")) - g_end) <= 5
        if exactish:
            exact_match_count += 1
        elif same_type:
            overlap_match_count += 1
        if same_type:
            type_match_count += 1
        else:
            type_mismatch_count += 1
            error_rows.append(
                {
                    "case_id": case_dir.name,
                    "error_type": "misclassification",
                    "gold_type": gold.get("type", ""),
                    "weak_type": best_row.get("type", ""),
                    "evidence_text": gold.get("text_span", ""),
                    "notes": "Weak-label span overlapped gold evidence but type differed.",
                }
            )

    extra_weak_count = max(0, len(weak_rows) - len(matched_weak))
    if extra_weak_count:
        for index, weak in enumerate(weak_rows):
            if index in matched_weak:
                continue
            text = str(weak.get("text_span", ""))
            error_type = "boilerplate_noise" if re.search(r"\b(forward-looking|may disconnect|operator|replay)\b", text, re.I) else "false_positive"
            error_rows.append(
                {
                    "case_id": case_dir.name,
                    "error_type": error_type,
                    "gold_type": "",
                    "weak_type": weak.get("type", ""),
                    "evidence_text": text,
                    "notes": "Weak label had no overlapping gold label in the starter benchmark.",
                }
            )
    return (
        {
            "case_id": case_dir.name,
            label_count_field: len(gold_rows),
            "weak_label_count": len(weak_rows),
            "matched_count": matched_count,
            "missed_gold_count": missed_gold_count,
            "extra_weak_count": extra_weak_count,
            "type_match_count": type_match_count,
            "type_mismatch_count": type_mismatch_count,
            "overlap_match_count": overlap_match_count,
            "exact_match_count": exact_match_count,
            "status": "evaluated",
        },
        error_rows,
    )


def evaluate_gold_corpus(
    root: Path,
    *,
    label_filename: str = "gold_labels.jsonl",
    require_human_label: bool = True,
    label_count_field: str = "gold_label_count",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for case_dir in active_case_dirs(root):
        row, case_errors = evaluate_case_labels(
            case_dir,
            label_filename=label_filename,
            require_human_label=require_human_label,
            label_count_field=label_count_field,
        )
        if row is not None:
            rows.append(row)
            errors.extend(case_errors)
    return rows, errors


def render_top_signals(case_id: str, signals: list[dict[str, Any]], guidance: list[dict[str, Any]]) -> str:
    lines = [f"# Top Signals: {case_id}", ""]
    for signal in signals[:5]:
        snippet = str(signal["evidence_text"]).replace("\n", " ")[:320]
        lines.extend(
            [
                f"## {signal['type']} ({signal['direction']}, {signal['confidence']})",
                f"- section: {signal['section']}",
                f"- speaker: {signal['speaker']}",
                f"- evidence: {snippet}",
                "",
            ]
        )
    if guidance:
        lines.append("## Guidance Summary")
        for item in guidance[:3]:
            lines.append(f"- {item['direction']}: {str(item['evidence_text'])[:220]}")
        lines.append("")
    return "\n".join(lines)


def render_demo(case_id: str, info: Any, signals: list[dict[str, Any]], guidance: list[dict[str, Any]]) -> str:
    lines = [
        f"# {info.ticker} {info.fiscal_year} {info.quarter}",
        "",
        "Transcript-derived signals only; not investment advice.",
        "",
        "## Key Signals",
    ]
    for signal in signals[:5]:
        lines.append(f"- {signal['type']}: {str(signal['evidence_text']).replace(chr(10), ' ')[:180]}")
    lines.extend(["", "## Guidance Summary"])
    if guidance:
        for item in guidance[:5]:
            lines.append(f"- {item['direction']}: {str(item['evidence_text'])[:180]}")
    else:
        lines.append("- No explicit deterministic guidance revision extracted.")
    lines.extend(["", "## Tone/Friction Summary"])
    counts = Counter(str(signal["type"]) for signal in signals)
    lines.append(f"- uncertainty={counts['uncertainty']}, analyst_pressure={counts['analyst_pressure']}, commitment={counts['commitment']}, risk_friction={counts['risk_friction']}")
    lines.extend(["", "## Evidence Quotes"])
    for signal in signals[:3]:
        lines.append(f"> {str(signal['evidence_text']).replace(chr(10), ' ')[:280]}")
    return "\n".join(lines) + "\n"


def status_from_guards(text: str, sections: dict[str, str], turns: list[dict[str, Any]], signals: list[dict[str, Any]], schema_errors: list[str]) -> tuple[str, str]:
    if len(text) < 10000:
        return "invalid", "transcript < 10,000 chars"
    if not sections.get("q_and_a"):
        return "invalid", "no Q&A section detected"
    if len({turn["speaker"] for turn in turns}) < 3:
        return "invalid", "fewer than 3 speakers detected"
    if not signals:
        return "invalid", "no signals extracted"
    if schema_errors:
        return "invalid", "schema issue: " + "; ".join(schema_errors[:3])
    return "success", ""


def quarantine_bad_cases(root: Path, audit: dict[str, dict[str, str]]) -> list[str]:
    duplicate_groups = read_csv_rows(root / "duplicate_transcripts.csv")
    duplicate_cases = {row["case_id"] for row in duplicate_groups}
    quarantine = root / "quarantine"
    moved: list[str] = []
    for case_dir in active_case_dirs(root):
        row = audit.get(case_dir.name, {})
        warnings = str(row.get("warnings", ""))
        should_move = (
            not boolish(row.get("likely_complete"))
            or "critical:" in warnings
            or case_dir.name in duplicate_cases
            or not (case_dir / "raw" / "transcript.txt").exists()
        )
        if should_move:
            quarantine.mkdir(exist_ok=True)
            target = quarantine / case_dir.name
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(case_dir), str(target))
            moved.append(case_dir.name)
    return moved


def process_case(case_dir: Path, info: Any) -> dict[str, Any]:
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    transcript = case_dir / "raw" / "transcript.txt"
    pdf = case_dir / "raw" / "transcript.pdf"
    raw_text = read_text(transcript)

    start = time.perf_counter()
    clean_text, cleaning_report = clean_transcript(raw_text)
    (case_dir / "clean").mkdir(exist_ok=True)
    (case_dir / "clean" / "transcript_clean.txt").write_text(clean_text, encoding="utf-8")
    write_json(case_dir / "clean" / "transcript_cleaning_report.json", cleaning_report)
    timings["cleaning_seconds"] = time.perf_counter() - start

    start = time.perf_counter()
    sections = split_sections(clean_text)
    (case_dir / "sections").mkdir(exist_ok=True)
    for name, value in sections.items():
        (case_dir / "sections" / f"{name}.txt").write_text(value + ("\n" if value else ""), encoding="utf-8")
    timings["sectioning_seconds"] = time.perf_counter() - start

    start = time.perf_counter()
    turns = speaker_turns(clean_text, sections)
    write_jsonl(case_dir / "speakers" / "speaker_turns.jsonl", turns)
    timings["speaker_extraction_seconds"] = time.perf_counter() - start

    start = time.perf_counter()
    guidance_rows = extract_guidance(info.case_id, clean_text)
    signals = extract_signals(info.case_id, clean_text, turns, guidance_rows)
    signals_payload = {"case_id": info.case_id, "signals": signals}
    schema_errors = validate_signals(info.case_id, signals_payload, len(clean_text))
    status, notes = status_from_guards(clean_text, sections, turns, signals, schema_errors)

    analysis_dir = case_dir / "analysis"
    labels_dir = case_dir / "labels"
    demo_dir = case_dir / "demo"
    for directory in (analysis_dir, labels_dir, demo_dir):
        directory.mkdir(exist_ok=True)
    write_json(analysis_dir / "signals.json", signals_payload)
    write_json(analysis_dir / "guidance.json", {"case_id": info.case_id, "guidance": guidance_rows})
    (analysis_dir / "top_signals.md").write_text(render_top_signals(info.case_id, signals, guidance_rows), encoding="utf-8")
    write_jsonl(labels_dir / "weak_labels.jsonl", weak_labels_from_signals(signals))
    scaffolded = write_gold_scaffold(case_dir, info.case_id)
    (demo_dir / "demo_summary.md").write_text(render_demo(info.case_id, info, signals, guidance_rows), encoding="utf-8")
    timings["analysis_seconds"] = time.perf_counter() - start

    source_type = source_type_for(case_dir, info)
    write_case_metadata(case_dir, info, source_type, transcript, pdf if pdf.exists() else None)
    timings["total_seconds"] = time.perf_counter() - total_start
    return {
        "case_id": info.case_id,
        "input_path": str(transcript),
        "output_path": str(analysis_dir / "signals.json"),
        "status": status,
        "notes": notes,
        "signals_count": len(signals),
        "guidance_count": len(guidance_rows),
        "weak_labels_count": len(signals),
        "gold_scaffolded": scaffolded,
        "demo_summary": str(demo_dir / "demo_summary.md"),
        "top_signals": str(analysis_dir / "top_signals.md"),
        "source_type": source_type,
        "pdf_path": str(pdf) if pdf.exists() else "",
        **timings,
    }


def corpus_manifest_rows(root: Path, source_map: dict[str, Any], analysis_rows: list[dict[str, Any]], audit: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    by_case = {row["case_id"]: row for row in analysis_rows}
    rows: list[dict[str, Any]] = []
    for case_dir in active_case_dirs(root):
        info = source_map.get(case_dir.name)
        if not info:
            continue
        analysis = by_case.get(case_dir.name, {})
        rows.append(
            {
                "case_id": info.case_id,
                "ticker": info.ticker,
                "fiscal_year": info.fiscal_year,
                "quarter": info.quarter,
                "source_type": source_type_for(case_dir, info),
                "source_url": info.source_url,
                "transcript_path": str(case_dir / "raw" / "transcript.txt"),
                "pdf_path": str(case_dir / "raw" / "transcript.pdf") if (case_dir / "raw" / "transcript.pdf").exists() else "",
                "quality_status": "pass" if boolish(audit.get(case_dir.name, {}).get("likely_complete")) else "warning",
                "analysis_status": analysis.get("status", "not_attempted"),
            }
        )
    return rows


def size_report_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_dir in active_case_dirs(root):
        transcript = case_dir / "raw" / "transcript.txt"
        text = read_text(transcript) if transcript.exists() else ""
        turn_count = len((case_dir / "speakers" / "speaker_turns.jsonl").read_text(encoding="utf-8").splitlines()) if (case_dir / "speakers" / "speaker_turns.jsonl").exists() else 0
        section_count = sum(1 for path in (case_dir / "sections").glob("*.txt") if path.read_text(encoding="utf-8").strip()) if (case_dir / "sections").exists() else 0
        rows.append({"case_id": case_dir.name, "char_count": len(text), "line_count": len(text.splitlines()), "estimated_tokens": math.ceil(len(text) / 4), "section_count": section_count, "speaker_turn_count": turn_count})
    return rows


def write_global_reports(root: Path, source_map: dict[str, Any], analysis_rows: list[dict[str, Any]], audit: dict[str, dict[str, str]], quarantined: list[str], hash_problems: list[str], grep_result: dict[str, Any], backup_path: Path) -> None:
    write_csv(root / "corpus_analysis_manifest.csv", analysis_rows, ["case_id", "input_path", "output_path", "status", "notes"])
    write_csv(root / "runtime_report.csv", analysis_rows, ["case_id", "total_seconds", "cleaning_seconds", "sectioning_seconds", "speaker_extraction_seconds", "analysis_seconds", "status"])
    manifest_rows = corpus_manifest_rows(root, source_map, analysis_rows, audit)
    write_csv(root / "transcripts_corpus_manifest.csv", manifest_rows, ["case_id", "ticker", "fiscal_year", "quarter", "source_type", "source_url", "transcript_path", "pdf_path", "quality_status", "analysis_status"])
    write_csv(root / "transcript_size_report.csv", size_report_rows(root), ["case_id", "char_count", "line_count", "estimated_tokens", "section_count", "speaker_turn_count"])

    index_rows: list[dict[str, Any]] = []
    for row in analysis_rows:
        case_dir = root / str(row["case_id"])
        info = source_map[str(row["case_id"])]
        signals_path = case_dir / "analysis" / "signals.json"
        signals = json.loads(signals_path.read_text(encoding="utf-8")).get("signals", []) if signals_path.exists() else []
        types = {str(signal.get("type")) for signal in signals}
        index_rows.append(
            {
                "case_id": info.case_id,
                "ticker": info.ticker,
                "sector": info.sector,
                "signals_count": len(signals),
                "has_guidance_revision": "guidance_revision" in types,
                "has_uncertainty": "uncertainty" in types,
                "has_analyst_pressure": "analyst_pressure" in types,
                "has_commitment": "commitment" in types,
                "analysis_status": row["status"],
            }
        )
    write_jsonl(root / "corpus_index.jsonl", index_rows)

    status_counts = Counter(str(row["status"]) for row in analysis_rows)
    weak_total = sum(int(row.get("weak_labels_count", 0)) for row in analysis_rows)
    lines = [
        "# Corpus Analysis Summary",
        "",
        f"- backup_path: {backup_path}",
        f"- active_case_folders: {len(active_case_dirs(root))}",
        f"- expected_active_cases: {EXPECTED_ACTIVE_CASES}",
        f"- quarantined_count: {len(quarantined)}",
        f"- analysis_success: {status_counts['success']}",
        f"- analysis_invalid: {status_counts['invalid']}",
        f"- analysis_failed: {status_counts['failed']}",
        f"- weak_labels_generated: {weak_total}",
        f"- raw_mutation_check: {'pass' if not hash_problems else 'fail'}",
        f"- excluded_reference_check: {'pass' if grep_result['passed'] else 'fail'}",
        "",
    ]
    (root / "corpus_analysis_summary.md").write_text("\n".join(lines), encoding="utf-8")

    top_lines = ["# Corpus Top Signals", ""]
    for row in analysis_rows:
        path = root / str(row["case_id"]) / "analysis" / "top_signals.md"
        if path.exists():
            top_lines.extend([f"## {row['case_id']}", ""])
            top_lines.extend(path.read_text(encoding="utf-8").splitlines()[2:10])
            top_lines.append("")
    (root / "corpus_top_signals.md").write_text("\n".join(top_lines), encoding="utf-8")

    demo_root = root / "demo"
    demo_root.mkdir(exist_ok=True)
    demo_lines = ["# Corpus Demo Summary", "", "Transcript-derived signals only; not investment advice.", ""]
    for row in analysis_rows:
        demo_lines.append(f"- {row['case_id']}: {row['status']}, signals={row['signals_count']}, guidance={row['guidance_count']}")
    (demo_root / "corpus_summary.md").write_text("\n".join(demo_lines) + "\n", encoding="utf-8")

    baseline_lines = [
        "# Baseline Comparison",
        "",
        "Naive baseline uses the first 500-1000 characters plus simple keyword extraction. Full analysis uses the full transcript and section/speaker context.",
        "",
        "| case_id | naive_hits | full_signals | section_coverage | evidence_quality |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in analysis_rows:
        case_dir = root / str(row["case_id"])
        text = read_text(case_dir / "raw" / "transcript.txt")
        naive = text[:1000].lower()
        naive_hits = sum(1 for term in ("guidance", "uncertain", "pressure", "confident", "risk") if term in naive)
        full = int(row["signals_count"])
        baseline_lines.append(f"| {row['case_id']} | {naive_hits} | {full} | full transcript | transcript evidence spans |")
    (root / "baseline_comparison.md").write_text("\n".join(baseline_lines) + "\n", encoding="utf-8")

    evaluation_rows, error_rows = evaluate_gold_corpus(root)
    write_csv(
        root / "label_evaluation.csv",
        evaluation_rows,
        [
            "case_id",
            "gold_label_count",
            "weak_label_count",
            "matched_count",
            "missed_gold_count",
            "extra_weak_count",
            "type_match_count",
            "type_mismatch_count",
            "overlap_match_count",
            "exact_match_count",
            "status",
        ],
    )
    write_csv(root / "label_error_details.csv", error_rows, ["case_id", "error_type", "gold_type", "weak_type", "evidence_text", "notes"])
    error_counts = Counter(str(row.get("error_type", "")) for row in error_rows)
    total_gold = sum(int(row["gold_label_count"]) for row in evaluation_rows)
    total_weak = sum(int(row["weak_label_count"]) for row in evaluation_rows)
    total_matched = sum(int(row["matched_count"]) for row in evaluation_rows)
    total_missed = sum(int(row["missed_gold_count"]) for row in evaluation_rows)
    total_extra = sum(int(row["extra_weak_count"]) for row in evaluation_rows)
    total_mismatch = sum(int(row["type_mismatch_count"]) for row in evaluation_rows)
    if evaluation_rows:
        analysis_text = [
            "# Label Error Analysis",
            "",
            "This is an early benchmark layer comparing deterministic weak labels with human-reviewed gold labels.",
            "It is not a production ML evaluation, does not claim statistical significance, and does not measure investment accuracy.",
            "",
            f"- active_cases: {len(active_case_dirs(root))}",
            f"- gold_labeled_cases: {len(evaluation_rows)}",
            f"- total_gold_labels: {total_gold}",
            f"- total_weak_labels_in_labeled_cases: {total_weak}",
            f"- matched_overlap_count: {total_matched}",
            f"- missed_gold_count: {total_missed}",
            f"- extra_weak_count: {total_extra}",
            f"- type_mismatch_count: {total_mismatch}",
            "",
            "Weak-label counts are not model accuracy, and no precision, recall, F1, alpha, or trading-edge claim is valid from this starter set.",
            "The current gold set is a starter benchmark, not a final statistically powered benchmark.",
            "",
            "## Error Themes",
        ]
        for key in ("false_positive", "missed_signal", "misclassification", "weak_evidence", "duplicate_signal", "schema_issue", "boilerplate_noise"):
            analysis_text.append(f"- {key}: {error_counts.get(key, 0)}")
        analysis_text.extend(
            [
                "",
                "## Recommended Rule Refinements",
                "",
                "- Reduce boilerplate/operator uncertainty matches before expanding the benchmark.",
                "- Review extra weak labels with no gold overlap for false-positive patterns.",
                "- Add neutral examples in each labeled case to test suppression behavior.",
                "- Expand each starter case to 15-25 human-reviewed labels before making stronger benchmark claims.",
            ]
        )
        (root / "label_error_analysis.md").write_text("\n".join(analysis_text) + "\n", encoding="utf-8")
    else:
        (root / "label_error_analysis.md").write_text("# Label Error Analysis\n\nGold-label evaluation found 0 valid non-empty human-reviewed label files in the active corpus. Weak-label outputs are deterministic scaffolds only.\n\nWeak-label counts are not model accuracy, and no precision, recall, F1, or statistical performance claim is valid until human-reviewed gold labels exist.\n", encoding="utf-8")

    draft_rows, draft_error_rows = evaluate_gold_corpus(
        root,
        label_filename="draft_gold_labels.jsonl",
        require_human_label=False,
        label_count_field="draft_label_count",
    )
    write_csv(
        root / "draft_label_evaluation.csv",
        draft_rows,
        [
            "case_id",
            "draft_label_count",
            "weak_label_count",
            "matched_count",
            "missed_gold_count",
            "extra_weak_count",
            "type_match_count",
            "type_mismatch_count",
            "overlap_match_count",
            "exact_match_count",
            "status",
        ],
    )
    write_csv(root / "draft_label_error_details.csv", draft_error_rows, ["case_id", "error_type", "gold_type", "weak_type", "evidence_text", "notes"])
    draft_total = sum(int(row["draft_label_count"]) for row in draft_rows)
    if draft_rows:
        draft_counts = Counter(str(row.get("error_type", "")) for row in draft_error_rows)
        draft_text = [
            "# Draft Label Evaluation",
            "",
            "This report compares deterministic weak labels with assistant-reviewed draft labels only.",
            "Draft labels are review-pending and are not final benchmark truth. Do not use this report for precision, recall, F1, statistical, or investment claims.",
            "",
            f"- draft_labeled_cases: {len(draft_rows)}",
            f"- total_draft_labels: {draft_total}",
            f"- matched_overlap_count: {sum(int(row['matched_count']) for row in draft_rows)}",
            f"- missed_draft_count: {sum(int(row['missed_gold_count']) for row in draft_rows)}",
            f"- extra_weak_count: {sum(int(row['extra_weak_count']) for row in draft_rows)}",
            f"- type_mismatch_count: {sum(int(row['type_mismatch_count']) for row in draft_rows)}",
            "",
            "## Draft Error Themes",
        ]
        for key in ("false_positive", "missed_signal", "misclassification", "weak_evidence", "duplicate_signal", "schema_issue", "boilerplate_noise"):
            draft_text.append(f"- {key}: {draft_counts.get(key, 0)}")
        (root / "draft_label_error_analysis.md").write_text("\n".join(draft_text) + "\n", encoding="utf-8")
    else:
        (root / "draft_label_error_analysis.md").write_text(
            "# Draft Label Evaluation\n\nNo draft_gold_labels.jsonl rows were available for draft-only evaluation.\n",
            encoding="utf-8",
        )
    labels_root = root / "labels"
    labels_root.mkdir(exist_ok=True)
    (labels_root / "gold_labeling_guide.md").write_text(
        "\n".join(
            [
                "# Gold Labeling Guide",
                "",
                "Use human review only. Do not create synthetic gold labels.",
                "",
                "Allowed label types: guidance_revision, uncertainty, analyst_pressure, commitment, neutral.",
                "",
                "Each JSONL row should include: type, text_span, start_char, end_char, reviewer, rationale.",
                "Character spans should point to the transcript text used for analysis.",
                "",
                "Add at least 5-10 reviewed labels per starter case before interpreting evaluation counts.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_json(
        root / "analysis_config_snapshot.json",
        {
            "timestamp": now_iso(),
            "corpus_root": str(root),
            "thresholds": {"min_audit_chars": 15000, "min_analysis_chars": 10000, "min_speakers": 3},
            "selection_criteria": "transcript exists, char_count >= 15000, likely_complete true, not quarantined",
            "scripts_used": ["audit_transcripts.py", "run_corpus_analysis.py"],
            "git_commit_hash": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root()), text=True).strip(),
            "rule_versions": {"deterministic_rules": "local_repo_current"},
        },
    )

    validation_lines = [
        "# Output Validation Report",
        "",
        f"- active_case_folders: {len(active_case_dirs(root))}",
        f"- expected_active_cases: {EXPECTED_ACTIVE_CASES}",
        f"- raw_hash_check: {'PASS' if not hash_problems else 'FAIL'}",
        f"- excluded_reference_check: {'PASS' if grep_result['passed'] else 'FAIL'}",
        f"- excluded_reference_hits: {len(grep_result['hits'])}",
        f"- quarantined_count: {len(quarantined)}",
        "",
    ]
    if hash_problems:
        validation_lines.extend(["## Raw Hash Problems", *[f"- {item}" for item in hash_problems], ""])
    if grep_result["hits"]:
        validation_lines.extend(["## Reference Hits", *[f"- {item}" for item in grep_result["hits"]], ""])
    (root / "output_validation_report.md").write_text("\n".join(validation_lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    source_map = load_sources()

    backup_path = backup_corpus(root)
    remove_excluded_case(root)
    scrub_excluded_references(root)
    audit = load_audit(root)
    quarantined = quarantine_bad_cases(root, audit)

    before = raw_hash_rows(root)
    write_csv(root / "raw_hash_manifest_before.csv", before, ["case_id", "path", "sha256"])

    analysis_rows: list[dict[str, Any]] = []
    for case_dir in active_case_dirs(root):
        info = source_map.get(case_dir.name)
        audit_row = audit.get(case_dir.name, {})
        if not info:
            continue
        if not boolish(audit_row.get("transcript_exists")) or int(audit_row.get("character_count") or 0) < 15000 or not boolish(audit_row.get("likely_complete")):
            analysis_rows.append({"case_id": case_dir.name, "input_path": str(case_dir / "raw" / "transcript.txt"), "output_path": "", "status": "invalid", "notes": "audit selection criteria failed", "signals_count": 0, "guidance_count": 0, "weak_labels_count": 0, "gold_scaffolded": False, "total_seconds": 0, "cleaning_seconds": 0, "sectioning_seconds": 0, "speaker_extraction_seconds": 0, "analysis_seconds": 0})
            continue
        try:
            analysis_rows.append(process_case(case_dir, info))
        except Exception as exc:
            analysis_rows.append({"case_id": case_dir.name, "input_path": str(case_dir / "raw" / "transcript.txt"), "output_path": "", "status": "failed", "notes": str(exc), "signals_count": 0, "guidance_count": 0, "weak_labels_count": 0, "gold_scaffolded": False, "total_seconds": 0, "cleaning_seconds": 0, "sectioning_seconds": 0, "speaker_extraction_seconds": 0, "analysis_seconds": 0})
            print(f"FAILED {case_dir.name}: {exc}", file=sys.stderr)

    after = raw_hash_rows(root)
    write_csv(root / "raw_hash_manifest_after.csv", after, ["case_id", "path", "sha256"])
    hash_problems = compare_hash_rows(before, after)
    grep_result = active_reference_grep(root)
    write_global_reports(root, source_map, analysis_rows, audit, quarantined, hash_problems, grep_result, backup_path)

    status_counts = Counter(str(row["status"]) for row in analysis_rows)
    print(
        "Analysis complete: "
        f"success={status_counts['success']} invalid={status_counts['invalid']} failed={status_counts['failed']} "
        f"quarantined={len(quarantined)} raw_hash={'pass' if not hash_problems else 'fail'} "
        f"excluded_refs={'pass' if grep_result['passed'] else 'fail'}"
    )
    return 1 if hash_problems or not grep_result["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
