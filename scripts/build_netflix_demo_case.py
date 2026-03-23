from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd
from pypdf import PdfReader

from earnings_call_sentiment import cli as cli_module
from earnings_call_sentiment.audio.summary import write_audio_behavior_outputs
from earnings_call_sentiment.pipeline.run import (
    DEFAULT_SENTIMENT_MODEL_NAME,
    DEFAULT_SENTIMENT_MODEL_REVISION,
    write_sentiment_artifacts,
    write_transcript_artifacts,
)
from earnings_call_sentiment.review_workflow import chunk_text_for_review, write_chunks_scored_artifacts
from earnings_call_sentiment.transcriber import transcribe_audio

logging.getLogger("pypdf").setLevel(logging.ERROR)

CASE_ID = "netflix_q1_2022"
CASE_LABEL = "Netflix Q1 2022"
EXPECTED_TRANSCRIPT_MARKER = "Netflix Q1 2022 Earnings Interview"
EXPECTED_TRANSCRIPT_QUARTER = "Q1 2022"
VIDEO_MISMATCH_ACTION = (
    "Uploaded video was verified as a Q2 2022 earnings interview, so video and audio were "
    "not bundled into the Q1 2022 demo case."
)
MANAGEMENT_SPEAKERS = {
    "Gregory K. Peters": "management",
    "Greg Peters": "management",
    "Spencer Wang": "management",
    "Spencer Adam Neumann": "management",
    "Spence Neumann": "management",
    "Theodore A. Sarandos": "management",
    "Ted Sarandos": "management",
    "Wilmot Reed Hastings": "management",
    "Reed Hastings": "management",
}
ANALYST_SPEAKERS = {
    "Douglas Till Anmuth": "analyst",
    "Doug Anmuth": "analyst",
}
KNOWN_SPEAKERS = {**MANAGEMENT_SPEAKERS, **ANALYST_SPEAKERS}
SECTION_PRESENTATION = "presentation"
SECTION_QA = "question_and_answer"


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_pdf_file(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return path.read_bytes().startswith(b"%PDF")
    except OSError:
        return False


def relative_to_case(path: Path, case_root: Path) -> str:
    return str(path.resolve().relative_to(case_root.resolve()))


def extract_pdf_pages(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return pages


def extract_pdf_text(path: Path) -> str:
    return "\n\n".join(extract_pdf_pages(path))


def discover_source_assets(source_dir: Path) -> dict[str, Any]:
    files = [path for path in sorted(source_dir.iterdir()) if path.is_file()]

    pdf_candidates = [path for path in files if is_pdf_file(path)]
    transcript_candidates = []
    transcript_duplicates: list[dict[str, Any]] = []
    canonical_transcript: Path | None = None
    canonical_md5: str | None = None
    for path in pdf_candidates:
        text = extract_pdf_text(path)[:5000]
        if "Netflix Q1 2022 Earnings Interview" in text or "FQ1 2022 Pre Recorded Earnings Call" in text:
            transcript_candidates.append(path)
    transcript_candidates = sorted(transcript_candidates, key=lambda item: item.name.lower())
    if not transcript_candidates:
        raise RuntimeError("Could not find a Netflix Q1 2022 transcript PDF in the source directory.")

    preferred = [path for path in transcript_candidates if "q1" in path.name.lower()]
    canonical_transcript = preferred[0] if preferred else transcript_candidates[0]
    canonical_md5 = md5_file(canonical_transcript)
    for path in transcript_candidates:
        if path == canonical_transcript:
            continue
        duplicate_md5 = md5_file(path)
        transcript_duplicates.append(
            {
                "filename": path.name,
                "md5": duplicate_md5,
                "same_as_canonical": duplicate_md5 == canonical_md5,
            }
        )

    shareholder_candidates = [
        path
        for path in pdf_candidates
        if "shareholder" in path.name.lower() or "fellow shareholders" in extract_pdf_text(path)[:2000].lower()
    ]
    if not shareholder_candidates:
        raise RuntimeError("Could not find a Netflix shareholder letter PDF in the source directory.")
    shareholder_letter = sorted(shareholder_candidates, key=lambda item: item.name.lower())[0]

    workbook_candidates = [path for path in files if path.suffix.lower() == ".xlsx"]
    if not workbook_candidates:
        raise RuntimeError("Could not find a Netflix financial workbook (.xlsx) in the source directory.")
    financial_workbook = workbook_candidates[0]

    csv_candidates = [path for path in files if path.suffix.lower() == ".csv"]
    income_statement_candidates = [
        path for path in csv_candidates if "income statement" in path.name.lower()
    ]
    if not income_statement_candidates:
        raise RuntimeError("Could not find a Netflix income statement CSV in the source directory.")
    income_statement_csv = income_statement_candidates[0]

    video_candidates = [path for path in files if path.suffix.lower() == ".mp4"]
    video_path = video_candidates[0] if video_candidates else None

    return {
        "transcript_pdf": canonical_transcript,
        "transcript_duplicates": transcript_duplicates,
        "shareholder_letter_pdf": shareholder_letter,
        "financial_workbook": financial_workbook,
        "income_statement_csv": income_statement_csv,
        "video_path": video_path,
        "raw_source_listing": [path.name for path in files],
    }


def ensure_scaffold(case_root: Path) -> dict[str, Path]:
    paths = {
        "case_root": case_root,
        "raw_transcript": case_root / "raw" / "transcript",
        "raw_shareholder": case_root / "raw" / "shareholder_letter",
        "raw_financials": case_root / "raw" / "financials",
        "raw_video": case_root / "raw" / "video",
        "raw_audio": case_root / "raw" / "audio",
        "processed_transcript": case_root / "processed" / "transcript_text",
        "processed_chunks": case_root / "processed" / "chunks",
        "processed_qa_pairs": case_root / "processed" / "qa_pairs",
        "processed_signals": case_root / "processed" / "signals",
        "processed_audio_behavior": case_root / "processed" / "audio_behavior",
        "processed_joined_review": case_root / "processed" / "joined_review",
        "demo_evidence": case_root / "demo" / "evidence_rows",
        "demo_summary": case_root / "demo" / "summary",
        "demo_fixtures": case_root / "demo" / "fixtures",
    }
    for path in paths.values():
        if path.suffix:
            continue
        path.mkdir(parents=True, exist_ok=True)
    return paths


def copy_raw_assets(
    source_assets: dict[str, Any],
    *,
    paths: dict[str, Path],
) -> dict[str, Path]:
    transcript_dest = paths["raw_transcript"] / "netflix_q1_2022_transcript.pdf"
    shareholder_dest = (
        paths["raw_shareholder"] / "netflix_q1_2022_shareholder_letter.pdf"
    )
    workbook_dest = paths["raw_financials"] / "netflix_q1_2022_financials.xlsx"
    income_csv_dest = paths["raw_financials"] / "netflix_q1_2022_income_statement.csv"
    shutil.copy2(source_assets["transcript_pdf"], transcript_dest)
    shutil.copy2(source_assets["shareholder_letter_pdf"], shareholder_dest)
    shutil.copy2(source_assets["financial_workbook"], workbook_dest)
    shutil.copy2(source_assets["income_statement_csv"], income_csv_dest)
    return {
        "transcript_pdf": transcript_dest,
        "shareholder_letter_pdf": shareholder_dest,
        "financial_workbook": workbook_dest,
        "income_statement_csv": income_csv_dest,
    }


def clean_transcript_pages(pages: list[str]) -> list[str]:
    lines: list[str] = []
    skip_patterns = [
        re.compile(r"^NETFLIX, INC\. FQ1 2022 PRE RECORDED EARNINGS CALL"),
        re.compile(r"^Copyright © 2022 S&P Global Market Intelligence"),
        re.compile(r"^spglobal\.com/marketintelligence"),
        re.compile(r"^\d+$"),
        re.compile(r"^CALL PARTICIPANTS$", re.I),
        re.compile(r"^EXECUTIVES$", re.I),
        re.compile(r"^ANALYSTS$", re.I),
    ]
    content_started = False
    for page in pages:
        for raw_line in page.splitlines():
            line = normalize_space(raw_line)
            if not line:
                continue
            if any(pattern.search(line) for pattern in skip_patterns):
                continue
            if line == "Presentation":
                content_started = True
                lines.append(line)
                continue
            if not content_started:
                continue
            lines.append(line)
    return lines


def is_title_line(line: str) -> bool:
    if not line:
        return False
    if line in KNOWN_SPEAKERS:
        return False
    if line.endswith(".") or line.endswith("?") or line.endswith("!"):
        return False
    title_keywords = (
        "Chief",
        "President",
        "Co-",
        "Vice President",
        "JPMorgan",
        "Research Division",
        "Chairman",
        "Director",
        "Officer",
        "Finance",
        "Corporate Development",
    )
    return any(keyword in line for keyword in title_keywords)


def build_speaker_blocks(lines: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_section = SECTION_PRESENTATION
    block_id = 0

    def flush_current() -> None:
        nonlocal current, block_id
        if current is None:
            return
        text = normalize_space(" ".join(current["text_parts"]))
        if text:
            current["text"] = text
            current["block_id"] = block_id
            current["speaker_title"] = normalize_space(" ".join(current["title_parts"]))
            current.pop("text_parts", None)
            current.pop("title_parts", None)
            blocks.append(current)
            block_id += 1
        current = None

    for line in lines:
        if line == "Presentation":
            current_section = SECTION_PRESENTATION
            continue
        if line == "Question and Answer":
            flush_current()
            current_section = SECTION_QA
            continue
        if line in KNOWN_SPEAKERS:
            flush_current()
            current = {
                "section": current_section,
                "speaker": line,
                "speaker_role": KNOWN_SPEAKERS[line],
                "title_parts": [],
                "text_parts": [],
            }
            continue
        if current is None:
            continue
        if not current["text_parts"] and is_title_line(line):
            current["title_parts"].append(line)
            continue
        current["text_parts"].append(line)

    flush_current()
    return blocks


def build_cleaned_transcript(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    last_section = None
    for block in blocks:
        section = block["section"]
        if section != last_section:
            lines.append("Presentation" if section == SECTION_PRESENTATION else "Question and Answer")
            last_section = section
        lines.append(f"{block['speaker']}: {block['text']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_synthetic_segments(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    segments: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    cursor = 0.0
    segment_id = 0
    for block in blocks:
        pieces = chunk_text_for_review(block["text"], max_chars=900)
        if not pieces:
            continue
        for piece in pieces:
            word_count = max(1, len(re.findall(r"\b\w+\b", piece)))
            duration_s = max(5.0, min(90.0, word_count / 2.6))
            start_s = round(cursor, 3)
            end_s = round(cursor + duration_s, 3)
            segments.append({"start": start_s, "end": end_s, "text": piece})
            metadata.append(
                {
                    "segment_id": segment_id,
                    "block_id": block["block_id"],
                    "section": block["section"],
                    "speaker": block["speaker"],
                    "speaker_role": block["speaker_role"],
                    "start": start_s,
                    "end": end_s,
                    "text": piece,
                }
            )
            cursor = end_s
            segment_id += 1
    return segments, metadata


def build_qa_pairs(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qa_pairs: list[dict[str, Any]] = []
    current_question: dict[str, Any] | None = None
    current_answers: list[dict[str, Any]] = []
    pair_id = 0
    for block in blocks:
        if block["section"] != SECTION_QA:
            continue
        if block["speaker_role"] == "analyst":
            if current_question is not None:
                qa_pairs.append(
                    {
                        "qa_pair_id": pair_id,
                        "question_speaker": current_question["speaker"],
                        "question_text": current_question["text"],
                        "answer_speakers": [item["speaker"] for item in current_answers],
                        "answer_text": normalize_space(" ".join(item["text"] for item in current_answers)),
                    }
                )
            pair_id += 1
            current_question = block
            current_answers = []
            continue
        if current_question is not None and block["speaker_role"] == "management":
            current_answers.append(block)
    if current_question is not None:
        qa_pairs.append(
            {
                "qa_pair_id": pair_id,
                "question_speaker": current_question["speaker"],
                "question_text": current_question["text"],
                "answer_speakers": [item["speaker"] for item in current_answers],
                "answer_text": normalize_space(" ".join(item["text"] for item in current_answers)),
            }
        )
    return qa_pairs


def normalize_paragraphs(text: str) -> list[str]:
    paragraphs = [normalize_space(part) for part in re.split(r"\n\s*\n", text) if normalize_space(part)]
    return paragraphs


def first_match(paragraphs: list[str], keywords: list[str]) -> str:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for paragraph in paragraphs:
        lowered = paragraph.lower()
        if all(keyword in lowered for keyword in lowered_keywords):
            return paragraph
    for paragraph in paragraphs:
        lowered = paragraph.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            return paragraph
    return ""


def build_shareholder_letter_evidence(text: str) -> dict[str, Any]:
    paragraphs = normalize_paragraphs(text)
    evidence = {
        "growth_slowdown": first_match(paragraphs, ["revenue growth has slowed"]),
        "account_sharing_and_monetization": first_match(
            paragraphs,
            ["sharing", "monetization"],
        ),
        "competitive_and_macro_headwinds": first_match(
            paragraphs,
            ["competition", "macro"],
        ),
        "forward_margin_framing": first_match(
            paragraphs,
            ["operating margin", "20%"],
        ),
        "paid_net_adds_or_outlook": first_match(
            paragraphs,
            ["paid net"],
        ),
    }
    return {
        "schema_version": "1.0.0",
        "paragraph_count": len(paragraphs),
        "evidence": evidence,
    }


def parse_money_value(text: str) -> float | None:
    cleaned = (
        text.replace("$", "")
        .replace(",", "")
        .replace("(", "-")
        .replace(")", "")
        .strip()
    )
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def build_financial_context_summary(csv_path: Path) -> dict[str, Any]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    normalized_rows = [[normalize_space(cell) for cell in row] for row in rows]

    def row_latest_value(index: int) -> float | None:
        if index < 0 or index >= len(normalized_rows):
            return None
        row = normalized_rows[index]
        for cell in reversed(row):
            if cell and re.search(r"\d", cell):
                return parse_money_value(cell)
        return None

    def find_row_index(first_col: str, second_col: str | None = None) -> int | None:
        first_col_lower = first_col.lower()
        second_col_lower = second_col.lower() if second_col else None
        for idx, row in enumerate(normalized_rows):
            left = row[0].lower() if row and row[0] else ""
            second = row[1].lower() if len(row) > 1 and row[1] else ""
            if left != first_col_lower:
                continue
            if second_col_lower is not None and second != second_col_lower:
                continue
            return idx
        return None

    revenue_idx = find_row_index("Revenues")
    operating_income_idx = find_row_index("Operating income")
    net_income_idx = find_row_index("Net income")
    diluted_eps_idx = None
    current_section = ""
    for idx, row in enumerate(normalized_rows):
        first = row[0] if row else ""
        second = row[1] if len(row) > 1 else ""
        if first:
            current_section = first
        if first == "" and second == "Diluted" and current_section == "Earnings per share:":
            diluted_eps_idx = idx
            break

    summary = {
        "schema_version": "1.0.0",
        "statement": "Consolidated Statements of Operations",
        "unit": "USD thousands except per-share data",
        "quarter_end": "2022-03-31",
        "metrics": {
            "revenue_usd_thousands": row_latest_value(revenue_idx if revenue_idx is not None else -1),
            "operating_income_usd_thousands": row_latest_value(
                operating_income_idx if operating_income_idx is not None else -1
            ),
            "net_income_usd_thousands": row_latest_value(net_income_idx if net_income_idx is not None else -1),
            "diluted_eps": row_latest_value(diluted_eps_idx if diluted_eps_idx is not None else -1),
        },
    }
    return summary


def find_block(blocks: list[dict[str, Any]], *, keywords: list[str], speaker: str | None = None) -> dict[str, Any] | None:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for block in blocks:
        if speaker and block["speaker"] != speaker:
            continue
        lowered = block["text"].lower()
        if all(keyword in lowered for keyword in lowered_keywords):
            return block
    for block in blocks:
        if speaker and block["speaker"] != speaker:
            continue
        lowered = block["text"].lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            return block
    return None


def extract_quote(text: str, *, max_chars: int = 320) -> str:
    compact = normalize_space(text)
    return compact if len(compact) <= max_chars else compact[: max_chars - 3] + "..."


def build_evidence_rows(
    *,
    case_root: Path,
    blocks: list[dict[str, Any]],
    shareholder_evidence: dict[str, Any],
    financial_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    signals_dir = case_root / "processed" / "signals"
    rows: list[dict[str, Any]] = []

    growth_block = find_block(
        blocks,
        keywords=["lower acquisition", "competition"],
        speaker="Wilmot Reed Hastings",
    )
    if growth_block:
        rows.append(
            {
                "row_id": "transcript_growth_headwinds",
                "source": "transcript",
                "section": growth_block["section"],
                "speaker": growth_block["speaker"],
                "speaker_role": growth_block["speaker_role"],
                "evidence_type": "management_framing",
                "quote": extract_quote(growth_block["text"]),
                "clear_signal": "Management explicitly ties weaker acquisition to account sharing, market penetration, and competition.",
                "remaining_ambiguity": "This is clear pressure framing, but not an explicit raised/maintained/lowered guidance action.",
                "artifact_paths": [
                    "processed/signals/uncertainty_signals.csv",
                    "processed/signals/analyst_skepticism.csv",
                    "processed/signals/report.md",
                ],
            }
        )

    q2_guide_block = find_block(
        blocks,
        keywords=["2Q guide", "loss of 2 million"],
        speaker="Spencer Adam Neumann",
    )
    if q2_guide_block:
        rows.append(
            {
                "row_id": "transcript_q2_paid_net_adds_guide",
                "source": "transcript",
                "section": q2_guide_block["section"],
                "speaker": q2_guide_block["speaker"],
                "speaker_role": q2_guide_block["speaker_role"],
                "evidence_type": "outlook",
                "quote": extract_quote(q2_guide_block["text"]),
                "clear_signal": "The Q&A explicitly references the Q2 paid net adds guide and the miss versus Q1 expectations.",
                "remaining_ambiguity": "The call explains the pressure drivers, but the longer-term recovery path is still qualified.",
                "artifact_paths": [
                    "processed/signals/guidance.csv",
                    "processed/signals/qa_shift_summary.json",
                    "processed/signals/report.md",
                ],
            }
        )

    sharing_block = find_block(
        blocks,
        keywords=["100 million households", "get paid"],
        speaker="Wilmot Reed Hastings",
    ) or find_block(
        blocks,
        keywords=["monetize sharing"],
        speaker="Gregory K. Peters",
    )
    if sharing_block:
        rows.append(
            {
                "row_id": "transcript_account_sharing_monetization",
                "source": "transcript",
                "section": sharing_block["section"],
                "speaker": sharing_block["speaker"],
                "speaker_role": sharing_block["speaker_role"],
                "evidence_type": "monetization_narrative",
                "quote": extract_quote(sharing_block["text"]),
                "clear_signal": "Management frames account sharing as a real monetization lever rather than a minor side topic.",
                "remaining_ambiguity": "The implementation path is iterative and timing is still qualified.",
                "artifact_paths": [
                    "processed/signals/guidance.csv",
                    "processed/signals/behavioral_summary.json",
                ],
            }
        )

    ads_block = find_block(
        blocks,
        keywords=["lower prices", "advertising"],
        speaker="Wilmot Reed Hastings",
    )
    if ads_block:
        rows.append(
            {
                "row_id": "transcript_ad_supported_option",
                "source": "transcript",
                "section": ads_block["section"],
                "speaker": ads_block["speaker"],
                "speaker_role": ads_block["speaker_role"],
                "evidence_type": "strategic_option",
                "quote": extract_quote(ads_block["text"]),
                "clear_signal": "Reed Hastings explicitly opens the door to a lower-priced ad-supported plan.",
                "remaining_ambiguity": "This is framed as an option under evaluation over the next 1 to 2 years, not a launched product.",
                "artifact_paths": [
                    "processed/signals/guidance.csv",
                    "processed/signals/report.md",
                ],
            }
        )

    for row_id, label in [
        ("letter_growth_slowdown", "growth_slowdown"),
        ("letter_account_sharing", "account_sharing_and_monetization"),
        ("letter_headwinds", "competitive_and_macro_headwinds"),
        ("letter_margin_framing", "forward_margin_framing"),
    ]:
        paragraph = shareholder_evidence["evidence"].get(label, "")
        if paragraph:
            rows.append(
                {
                    "row_id": row_id,
                    "source": "shareholder_letter",
                    "section": "shareholder_letter",
                    "speaker": "Netflix shareholder letter",
                    "speaker_role": "management_document",
                    "evidence_type": label,
                    "quote": extract_quote(paragraph),
                    "clear_signal": "The shareholder letter provides explicit management framing that supports the call narrative.",
                    "remaining_ambiguity": "The letter is still management-authored framing, not an external validation layer.",
                    "artifact_paths": [
                        "processed/signals/shareholder_letter_evidence.json",
                    ],
                }
            )

    metrics = financial_summary["metrics"]
    rows.append(
        {
            "row_id": "financial_context_q1_2022",
            "source": "financials",
            "section": "income_statement",
            "speaker": "Netflix Q1 2022 financials",
            "speaker_role": "financial_context",
            "evidence_type": "headline_metrics",
            "quote": (
                f"Revenue: {metrics['revenue_usd_thousands']:,.0f} (USD thousands); "
                f"Operating income: {metrics['operating_income_usd_thousands']:,.0f}; "
                f"Net income: {metrics['net_income_usd_thousands']:,.0f}; "
                f"Diluted EPS: {metrics['diluted_eps']:.2f}."
            ),
            "clear_signal": "The uploaded financial files anchor the case to the March 31, 2022 quarter with concrete reported results.",
            "remaining_ambiguity": "These figures provide context for the demo, not a standalone predictive signal.",
            "artifact_paths": [
                "processed/signals/financial_context_summary.json",
            ],
        }
    )

    return rows


def build_joined_review_moments(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for row in evidence_rows:
        if row["row_id"] in {
            "transcript_growth_headwinds",
            "transcript_q2_paid_net_adds_guide",
            "transcript_account_sharing_monetization",
            "letter_growth_slowdown",
            "financial_context_q1_2022",
        }:
            selected.append(row)
    return selected[:5]


def verify_video_quarter(video_path: Path | None) -> dict[str, Any]:
    if video_path is None or not video_path.exists():
        return {
            "status": "missing",
            "expected_quarter": EXPECTED_TRANSCRIPT_QUARTER,
            "action": "No uploaded video asset was available, so audio hooks stayed disabled.",
        }

    with tempfile.TemporaryDirectory(prefix="netflix-video-verify-") as temp_dir:
        intro_audio = Path(temp_dir) / "intro.wav"
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "0",
            "-t",
            "75",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(intro_audio),
        ]
        proc = subprocess.run(ffmpeg_cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            return {
                "status": "error",
                "video_filename": video_path.name,
                "expected_quarter": EXPECTED_TRANSCRIPT_QUARTER,
                "action": "Video verification failed before audio hooks could run.",
                "error": ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip(),
            }
        intro_segments = transcribe_audio(
            str(intro_audio),
            verbose=False,
            model_name="tiny",
            device="cpu",
            compute_type="int8",
        )
    intro_excerpt = normalize_space(" ".join(segment.get("text", "") for segment in intro_segments[:5]))
    lowered = intro_excerpt.lower()
    if "q1 2022" in lowered:
        detected = "Q1 2022"
        consistent = True
        status = "verified"
        action = "Quarter-consistent video can be used for optional audio hooks."
    elif "q2" in lowered:
        detected = "Q2 2022"
        consistent = False
        status = "mismatch"
        action = VIDEO_MISMATCH_ACTION
    else:
        detected = "unknown"
        consistent = False
        status = "unclear"
        action = "Video intro did not cleanly verify the quarter, so audio hooks stayed disabled."
    return {
        "status": status,
        "expected_quarter": EXPECTED_TRANSCRIPT_QUARTER,
        "detected_quarter": detected,
        "quarter_consistent": consistent,
        "video_filename": video_path.name,
        "video_md5": md5_file(video_path),
        "duration_s": round(_video_duration(video_path), 3),
        "intro_excerpt": intro_excerpt,
        "action": action,
    }


def _video_duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return 0.0
    try:
        return float((proc.stdout or "0").strip())
    except ValueError:
        return 0.0


def build_audio_status(
    *,
    paths: dict[str, Path],
    video_verification: dict[str, Any],
) -> dict[str, Any]:
    summary_path = paths["processed_audio_behavior"] / "audio_status.json"
    if video_verification.get("quarter_consistent"):
        raw_video = paths["raw_video"] / "netflix_q1_2022_video.mp4"
        raw_audio = paths["raw_audio"] / "netflix_q1_2022_audio.wav"
        shutil.copy2(Path(str(video_verification["source_video_path"])), raw_video)
        proc = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_video),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(raw_audio),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            qa_segments_path = paths["processed_signals"] / "qa_shift_segments.csv"
            qa_segments_df = pd.read_csv(qa_segments_path) if qa_segments_path.exists() else pd.DataFrame()
            audio_outputs = write_audio_behavior_outputs(
                raw_audio,
                qa_segments_df,
                paths["processed_audio_behavior"],
            )
            status = {
                "status": "generated",
                "audio_behavior_summary_path": relative_to_case(audio_outputs["summary_path"], paths["case_root"]),
                "audio_behavior_segments_path": relative_to_case(audio_outputs["segments_path"], paths["case_root"]),
                "audio_path": relative_to_case(raw_audio, paths["case_root"]),
                "video_path": relative_to_case(raw_video, paths["case_root"]),
                "reason": "Quarter-consistent video was available.",
            }
            summary_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
            return status

    status = {
        "status": "skipped",
        "reason": VIDEO_MISMATCH_ACTION
        if video_verification.get("status") == "mismatch"
        else "No quarter-consistent video was available for the Q1 2022 demo case.",
        "video_verification": {
            key: value
            for key, value in video_verification.items()
            if key != "source_video_path"
        },
        "expected_audio_target": "raw/audio/netflix_q1_2022_audio.wav",
    }
    summary_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status


def build_quarter_consistency(
    *,
    raw_assets: dict[str, Path],
    source_assets: dict[str, Any],
    shareholder_text: str,
    financial_summary: dict[str, Any],
    video_verification: dict[str, Any],
) -> dict[str, Any]:
    transcript_text = extract_pdf_text(raw_assets["transcript_pdf"])
    transcript_detected = (
        "Q1 2022"
        if "FQ1 2022 Pre Recorded Earnings Call" in transcript_text
        and EXPECTED_TRANSCRIPT_MARKER in transcript_text
        else "unknown"
    )
    shareholder_detected = (
        "Q1 2022"
        if "April 19, 2022" in shareholder_text
        and "revenue growth has slowed considerably" in shareholder_text.lower()
        else "unknown"
    )
    financial_detected = (
        "Q1 2022"
        if math.isclose(float(financial_summary["metrics"]["diluted_eps"] or 0.0), 3.53, rel_tol=0.0, abs_tol=0.01)
        else "unknown"
    )
    video_status = video_verification.get("status")
    if video_status == "mismatch":
        overall_status = "transcript_first_ready_video_skipped"
        action_taken = (
            "Built the fixed Q1 2022 transcript-first demo case from transcript, shareholder letter, and financials. "
            "Skipped video/audio because the uploaded video verified as Q2."
        )
    elif video_status == "verified":
        overall_status = "transcript_first_ready_video_available"
        action_taken = (
            "Built the fixed Q1 2022 transcript-first demo case from transcript, shareholder letter, and financials, "
            "with quarter-consistent media available as an optional supporting layer."
        )
    else:
        overall_status = "transcript_first_ready"
        action_taken = (
            "Built the fixed Q1 2022 transcript-first demo case from transcript, shareholder letter, and financials. "
            "No quarter-consistent video was available for optional audio hooks."
        )
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "expected_case_quarter": EXPECTED_TRANSCRIPT_QUARTER,
        "transcript": {
            "status": "verified" if transcript_detected == EXPECTED_TRANSCRIPT_QUARTER else "unclear",
            "detected_quarter": transcript_detected,
            "canonical_filename": raw_assets["transcript_pdf"].name,
            "canonical_md5": md5_file(raw_assets["transcript_pdf"]),
            "supporting_text": EXPECTED_TRANSCRIPT_MARKER,
            "mislabeled_duplicates": source_assets["transcript_duplicates"],
        },
        "shareholder_letter": {
            "status": "verified" if shareholder_detected == EXPECTED_TRANSCRIPT_QUARTER else "unclear",
            "detected_quarter": shareholder_detected,
            "filename": raw_assets["shareholder_letter_pdf"].name,
            "supporting_text": "April 19, 2022 letter discussing slowing revenue growth and Q1 results.",
        },
        "financials": {
            "status": "verified" if financial_detected == EXPECTED_TRANSCRIPT_QUARTER else "unclear",
            "detected_quarter": financial_detected,
            "workbook_filename": raw_assets["financial_workbook"].name,
            "income_statement_filename": raw_assets["income_statement_csv"].name,
            "supporting_text": "Income statement latest quarter column ends at March 31, 2022.",
        },
        "video": {
            key: value
            for key, value in video_verification.items()
            if key != "source_video_path"
        },
        "overall_status": overall_status,
        "action_taken": action_taken,
    }


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def build_demo_summary(
    *,
    case_root: Path,
    quarter_consistency: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    qa_pairs: list[dict[str, Any]],
    audio_status: dict[str, Any],
) -> dict[str, Any]:
    signals_dir = case_root / "processed" / "signals"
    metrics = json.loads((signals_dir / "metrics.json").read_text(encoding="utf-8"))
    guidance_df = read_csv_or_empty(signals_dir / "guidance.csv")
    uncertainty_df = read_csv_or_empty(signals_dir / "uncertainty_signals.csv")
    skepticism_df = read_csv_or_empty(signals_dir / "analyst_skepticism.csv")
    video_status = quarter_consistency.get("video", {}).get("status")
    if video_status == "mismatch":
        video_summary_point = (
            "The uploaded video is a Q2 earnings interview and was skipped instead of being mixed into the Q1 case."
        )
    elif video_status == "verified":
        video_summary_point = "Quarter-consistent media is available as optional supporting context."
    else:
        video_summary_point = (
            "No quarter-consistent video was bundled into this fixed demo package, so the transcript-first path remains primary."
        )
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "display_name": CASE_LABEL,
        "quarter": EXPECTED_TRANSCRIPT_QUARTER,
        "quarter_consistency": quarter_consistency,
        "transcript_first_status": "ready",
        "audio_status": audio_status,
        "headline_counts": {
            "guidance_rows": int(len(guidance_df)),
            "uncertainty_rows": int(len(uncertainty_df)),
            "analyst_skepticism_rows": int(len(skepticism_df)),
            "qa_pairs": int(len(qa_pairs)),
            "evidence_rows": int(len(evidence_rows)),
        },
        "review_scorecard": metrics.get("review_scorecard", {}),
        "top_summary_points": [
            "Q1 2022 transcript, shareholder letter, and financial files are quarter-consistent.",
            video_summary_point,
            "The transcript-first bundle surfaces explicit growth-slowdown framing, paid net adds pressure, and monetization/account-sharing discussion.",
        ],
        "limitations": [
            "This is a transcript-first deterministic review package, not a predictive or trading system.",
            "Audio and video are supporting layers only and were skipped here because the uploaded media was not quarter-consistent.",
            "Synthetic transcript timing is only used to make deterministic artifacts runnable; it is not real media timing.",
        ],
    }


def build_fixture(
    *,
    case_root: Path,
    quarter_consistency: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    audio_status: dict[str, Any],
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "display_name": CASE_LABEL,
        "quarter": EXPECTED_TRANSCRIPT_QUARTER,
        "case_status": summary["quarter_consistency"]["overall_status"],
        "quarter_consistency": quarter_consistency,
        "artifact_paths": {
            "transcript_cleaned": "processed/transcript_text/transcript_cleaned.txt",
            "transcript_sectioned": "processed/transcript_text/transcript_sectioned.json",
            "qa_pairs": "processed/qa_pairs/qa_pairs.json",
            "guidance": "processed/signals/guidance.csv",
            "guidance_revision": "processed/signals/guidance_revision.csv",
            "uncertainty": "processed/signals/uncertainty_signals.csv",
            "analyst_skepticism": "processed/signals/analyst_skepticism.csv",
            "qa_shift_summary": "processed/signals/qa_shift_summary.json",
            "financial_context_summary": "processed/signals/financial_context_summary.json",
            "shareholder_letter_evidence": "processed/signals/shareholder_letter_evidence.json",
            "audio_status": "processed/audio_behavior/audio_status.json",
            "quarter_consistency": "processed/joined_review/quarter_consistency.json",
        },
        "evidence_rows_preview": evidence_rows[:6],
        "audio_status": audio_status,
        "notes": [
            "Transcript-first artifacts are the source of truth for this demo case.",
            "Later UI work can consume this fixture directly without running the full live pipeline.",
        ],
    }


def build_demo_case(
    *,
    case_root: Path,
    source_dir: Path | None,
) -> dict[str, Any]:
    paths = ensure_scaffold(case_root)

    if source_dir is not None:
        source_assets = discover_source_assets(source_dir)
        raw_assets = copy_raw_assets(source_assets, paths=paths)
    else:
        prior_quarter_consistency = load_json_if_exists(
            paths["processed_joined_review"] / "quarter_consistency.json"
        )
        prior_video_verification = load_json_if_exists(paths["raw_video"] / "video_verification.json")
        raw_assets = {
            "transcript_pdf": paths["raw_transcript"] / "netflix_q1_2022_transcript.pdf",
            "shareholder_letter_pdf": paths["raw_shareholder"] / "netflix_q1_2022_shareholder_letter.pdf",
            "financial_workbook": paths["raw_financials"] / "netflix_q1_2022_financials.xlsx",
            "income_statement_csv": paths["raw_financials"] / "netflix_q1_2022_income_statement.csv",
        }
        missing = [str(path) for path in raw_assets.values() if not path.exists()]
        if missing:
            raise RuntimeError(
                "Raw Netflix demo assets are missing. Re-run with --source-dir or add the expected raw files: "
                + ", ".join(missing)
            )
        source_assets = {
            "transcript_duplicates": (
                prior_quarter_consistency.get("transcript", {}).get("mislabeled_duplicates", [])
                if prior_quarter_consistency
                else []
            ),
            "video_path": None,
            "raw_source_listing": [],
            "saved_video_verification": prior_video_verification
            or (prior_quarter_consistency.get("video") if prior_quarter_consistency else None),
        }

    transcript_pages = extract_pdf_pages(raw_assets["transcript_pdf"])
    transcript_raw_text = "\n\n".join(
        f"=== PAGE {index + 1} ===\n{page}" for index, page in enumerate(transcript_pages)
    )
    cleaned_lines = clean_transcript_pages(transcript_pages)
    blocks = build_speaker_blocks(cleaned_lines)
    cleaned_transcript = build_cleaned_transcript(blocks)
    segments, segment_metadata = build_synthetic_segments(blocks)
    qa_pairs = build_qa_pairs(blocks)

    transcript_dir = paths["processed_transcript"]
    transcript_dir.mkdir(parents=True, exist_ok=True)
    (transcript_dir / "transcript_raw_extract.txt").write_text(
        transcript_raw_text,
        encoding="utf-8",
    )
    (transcript_dir / "transcript_cleaned.txt").write_text(
        cleaned_transcript,
        encoding="utf-8",
    )
    write_json(transcript_dir / "transcript_sectioned.json", {"blocks": blocks})
    write_json(paths["processed_qa_pairs"] / "qa_pairs.json", {"qa_pairs": qa_pairs})
    write_json(paths["processed_chunks"] / "segment_metadata.json", {"segments": segment_metadata})
    write_transcript_artifacts(segments, transcript_dir)

    shareholder_text = extract_pdf_text(raw_assets["shareholder_letter_pdf"])
    (transcript_dir / "shareholder_letter_text.txt").write_text(
        shareholder_text,
        encoding="utf-8",
    )
    shareholder_evidence = build_shareholder_letter_evidence(shareholder_text)
    financial_summary = build_financial_context_summary(raw_assets["income_statement_csv"])

    signals_dir = paths["processed_signals"]
    artifacts = write_sentiment_artifacts(
        segments=segments,
        output_path=signals_dir,
        verbose=False,
        sentiment_model=DEFAULT_SENTIMENT_MODEL_NAME,
        sentiment_revision=DEFAULT_SENTIMENT_MODEL_REVISION,
    )
    chunks_scored_df, _, _ = write_chunks_scored_artifacts(
        paths["processed_chunks"],
        artifacts["sentiment_segments"],
    )
    postscore_args = SimpleNamespace(
        resume=False,
        force=True,
        prior_guidance=None,
        tone_change_threshold=2.0,
        sentiment_model=DEFAULT_SENTIMENT_MODEL_NAME,
        sentiment_revision=DEFAULT_SENTIMENT_MODEL_REVISION,
    )
    cli_module._run_postscore_stages(
        chunks_scored_df=chunks_scored_df,
        out_dir=signals_dir,
        args=postscore_args,
    )
    write_json(signals_dir / "shareholder_letter_evidence.json", shareholder_evidence)
    write_json(signals_dir / "financial_context_summary.json", financial_summary)

    if source_assets.get("video_path") is not None:
        video_verification = verify_video_quarter(source_assets.get("video_path"))
        video_verification["source_video_path"] = str(source_assets["video_path"])
    else:
        video_verification = source_assets.get("saved_video_verification") or verify_video_quarter(None)
    write_json(paths["raw_video"] / "video_verification.json", {key: value for key, value in video_verification.items() if key != "source_video_path"})

    audio_status = build_audio_status(paths=paths, video_verification=video_verification)
    quarter_consistency = build_quarter_consistency(
        raw_assets=raw_assets,
        source_assets=source_assets,
        shareholder_text=shareholder_text,
        financial_summary=financial_summary,
        video_verification=video_verification,
    )
    write_json(paths["processed_joined_review"] / "quarter_consistency.json", quarter_consistency)

    evidence_rows = build_evidence_rows(
        case_root=case_root,
        blocks=blocks,
        shareholder_evidence=shareholder_evidence,
        financial_summary=financial_summary,
    )
    summary = build_demo_summary(
        case_root=case_root,
        quarter_consistency=quarter_consistency,
        evidence_rows=evidence_rows,
        qa_pairs=qa_pairs,
        audio_status=audio_status,
    )
    fixture = build_fixture(
        case_root=case_root,
        quarter_consistency=quarter_consistency,
        evidence_rows=evidence_rows,
        summary=summary,
        audio_status=audio_status,
    )
    joined_review = {
        "case_id": CASE_ID,
        "joined_review_moments": build_joined_review_moments(evidence_rows),
        "audio_status": audio_status,
    }

    write_json(paths["processed_joined_review"] / "joined_review_moments.json", joined_review)
    write_json(paths["demo_evidence"] / "netflix_demo_evidence_rows.json", {"rows": evidence_rows})
    write_json(paths["demo_summary"] / "netflix_demo_summary.json", summary)
    write_json(paths["demo_fixtures"] / "netflix_demo_fixture.json", fixture)

    return {
        "case_root": case_root,
        "quarter_consistency_path": paths["processed_joined_review"] / "quarter_consistency.json",
        "evidence_rows_path": paths["demo_evidence"] / "netflix_demo_evidence_rows.json",
        "summary_path": paths["demo_summary"] / "netflix_demo_summary.json",
        "fixture_path": paths["demo_fixtures"] / "netflix_demo_fixture.json",
        "audio_status_path": paths["processed_audio_behavior"] / "audio_status.json",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the fixed Netflix Q1 2022 transcript-first demo case bundle. "
            "The script copies correct-quarter raw assets into the repo-local scaffold, "
            "verifies quarter consistency, generates deterministic transcript-first artifacts, "
            "and only enables audio hooks if a quarter-consistent video is supplied."
        )
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing the uploaded Netflix assets. When omitted, the script rebuilds "
            "from repo-local raw assets already stored under data/demo_cases/netflix_q1_2022/raw/."
        ),
    )
    parser.add_argument(
        "--case-root",
        type=Path,
        default=Path("data/demo_cases/netflix_q1_2022"),
        help="Repo-local case root for the fixed Netflix demo package.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source_dir = args.source_dir.expanduser().resolve() if args.source_dir else None
    case_root = args.case_root.expanduser().resolve()
    outputs = build_demo_case(case_root=case_root, source_dir=source_dir)
    print(f"Netflix demo case built at: {case_root}")
    print(f"Quarter consistency: {outputs['quarter_consistency_path']}")
    print(f"Evidence rows: {outputs['evidence_rows_path']}")
    print(f"Summary: {outputs['summary_path']}")
    print(f"Fixture: {outputs['fixture_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
