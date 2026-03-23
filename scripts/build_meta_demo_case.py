from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import subprocess
import wave
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

CASE_ID = "meta_q3_2022"
CASE_LABEL = "Meta Q3 2022"
EXPECTED_QUARTER = "Q3 2022"
EVENT_DATE = "2022-10-26"
AUDIO_ALIGNMENT_NOTE = (
    "Audio timings are attached only to a few curated Q&A moments matched against an ASR transcript. "
    "They are supporting review cues, not full transcript-to-video alignment."
)

SECTION_PRESENTATION = "presentation"
SECTION_QA = "question_and_answer"

MANAGEMENT_SPEAKERS = {
    "Deborah Crawford": "management",
    "Mark Zuckerberg": "management",
    "Dave Wehner": "management",
    "David Wehner": "management",
    "Susan Li": "management",
    "Marne Levine": "management",
}

TITLE_KEYWORDS = (
    "chief",
    "ceo",
    "cfo",
    "finance",
    "investor relations",
    "business officer",
    "vice president",
    "vp",
)

HEDGE_MARKER_PATTERNS = (
    ("i think", re.compile(r"\bi think\b")),
    ("maybe", re.compile(r"\bmaybe\b")),
    ("probably", re.compile(r"\bprobably\b")),
    ("kind of", re.compile(r"\bkind of\b")),
    ("sort of", re.compile(r"\bsort of\b")),
    ("we believe", re.compile(r"\bwe believe\b")),
    ("we expect", re.compile(r"\bwe expect\b")),
    ("not clear", re.compile(r"\bnot clear\b")),
    ("optimistic", re.compile(r"\boptimistic\b")),
    ("would", re.compile(r"\bwould\b")),
    ("could", re.compile(r"\bcould\b")),
    ("should", re.compile(r"\bshould\b")),
)

AUDIO_TARGET_SPECS = [
    {
        "row_id": "qa_capex_ai_pressure_audio",
        "plain_english_label": "analyst pushback on AI capex",
        "review_priority": "high",
        "why_it_matters": (
            "This is the clearest direct challenge on elevated AI infrastructure spending and expected returns."
        ),
        "question_keywords": ["capex", "return on invested capital", "ai investments"],
        "answer_keywords": ["ai", "infrastructure", "engagement", "revenue"],
    },
    {
        "row_id": "qa_reels_headwind_audio",
        "plain_english_label": "qualified answer on Reels monetization",
        "review_priority": "high",
        "why_it_matters": (
            "This is a strong demo moment because management acknowledges a material monetization headwind while "
            "keeping the improvement timeline qualified."
        ),
        "question_keywords": ["reels", "monetization"],
        "answer_keywords": ["500 million", "12 to 18 months", "neutral"],
    },
    {
        "row_id": "qa_efficiency_spending_audio",
        "plain_english_label": "qualified answer on efficiency and spending discipline",
        "review_priority": "high",
        "why_it_matters": (
            "This is a useful side-by-side moment because management pairs cost discipline language with still-heavy "
            "investment commitments."
        ),
        "question_keywords": ["expense", "efficiency", "spending", "headcount"],
        "answer_keywords": ["2023", "flat", "slightly smaller", "expense", "headcount"],
    },
]


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def relative_to_case(path: Path, case_root: Path) -> str:
    return str(path.resolve().relative_to(case_root.resolve()))


def extract_pdf_pages(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def extract_pdf_text(path: Path) -> str:
    return "\n\n".join(extract_pdf_pages(path))


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


def extract_quote(text: str, *, max_chars: int = 320) -> str:
    compact = normalize_space(text)
    return compact if len(compact) <= max_chars else compact[: max_chars - 3] + "..."


def ensure_scaffold(case_root: Path) -> dict[str, Path]:
    paths = {
        "case_root": case_root,
        "raw_transcript": case_root / "raw" / "transcript",
        "raw_follow_up_transcript": case_root / "raw" / "follow_up_transcript",
        "raw_results_release": case_root / "raw" / "results_release",
        "raw_presentation": case_root / "raw" / "presentation",
        "raw_video": case_root / "raw" / "video",
        "raw_audio": case_root / "raw" / "audio",
        "processed_transcript": case_root / "processed" / "transcript_text",
        "processed_follow_up": case_root / "processed" / "follow_up_text",
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
        path.mkdir(parents=True, exist_ok=True)
    return paths


def expected_raw_assets(paths: dict[str, Path]) -> dict[str, Path]:
    return {
        "transcript_pdf": paths["raw_transcript"] / "meta_q3_2022_earnings_call_transcript.pdf",
        "follow_up_pdf": paths["raw_follow_up_transcript"] / "meta_q3_2022_follow_up_call_transcript.pdf",
        "results_release_pdf": paths["raw_results_release"] / "meta_q3_2022_results_release.pdf",
        "presentation_pdf": paths["raw_presentation"] / "meta_q3_2022_earnings_presentation.pdf",
        "video_path": paths["raw_video"] / "meta_q3_2022_video.mp4",
        "audio_path": paths["raw_audio"] / "meta_q3_2022_audio.wav",
    }


def clean_main_transcript_pages(pages: list[str]) -> list[str]:
    lines: list[str] = []
    skip_patterns = [
        re.compile(r"^\d+$"),
        re.compile(r"^Meta Platforms, Inc\. \(META\)$"),
        re.compile(r"^Third Quarter 2022 Results Conference Call$"),
        re.compile(r"^October 26th, 2022$"),
    ]
    content_started = False
    for page in pages:
        for raw_line in page.splitlines():
            line = normalize_space(raw_line)
            if not line:
                continue
            if any(pattern.search(line) for pattern in skip_patterns):
                continue
            if line == "Deborah Crawford, VP, Investor Relations":
                content_started = True
            if not content_started:
                continue
            lines.append(line)
    return lines


def clean_follow_up_pages(pages: list[str]) -> list[str]:
    lines: list[str] = []
    skip_patterns = [
        re.compile(r"^\d+$"),
        re.compile(r"^Meta Platforms, Inc\. \(META\)$"),
        re.compile(r"^Third Quarter 2022 Follow Up Call$"),
        re.compile(r"^October 26th, 2022$"),
    ]
    content_started = False
    for page in pages:
        for raw_line in page.splitlines():
            line = normalize_space(raw_line)
            if not line:
                continue
            if any(pattern.search(line) for pattern in skip_patterns):
                continue
            if line.startswith("Operator:"):
                content_started = True
            if not content_started:
                continue
            lines.append(line)
    return lines


def is_title_line(line: str) -> bool:
    lowered = line.lower()
    return any(keyword in lowered for keyword in TITLE_KEYWORDS)


def _speaker_role_for(speaker: str, *, section: str, title: str = "") -> str:
    if speaker == "Operator":
        return "operator"
    if speaker in MANAGEMENT_SPEAKERS:
        return MANAGEMENT_SPEAKERS[speaker]
    if title and is_title_line(title):
        return "management"
    if section == SECTION_QA:
        return "analyst"
    return "other"


def build_speaker_blocks(lines: list[str], *, source_doc: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_section = SECTION_PRESENTATION
    block_id = 0

    colon_pattern = re.compile(r"^([A-Z][A-Za-z .&'’/-]{1,80}?):\s*(.*)$")
    heading_pattern = re.compile(r"^([A-Z][A-Za-z .&'’/-]{1,80}?),(.+)$")

    def flush_current() -> None:
        nonlocal current, block_id
        if current is None:
            return
        text = normalize_space(" ".join(current["text_parts"]))
        if text:
            current["text"] = text
            current["block_id"] = block_id
            current.pop("text_parts", None)
            blocks.append(current)
            block_id += 1
        current = None

    for line in lines:
        if "question and answer session" in line.lower():
            flush_current()
            current_section = SECTION_QA
            if line.startswith("Operator:"):
                current = {
                    "source_doc": source_doc,
                    "section": SECTION_QA,
                    "speaker": "Operator",
                    "speaker_role": "operator",
                    "speaker_title": "",
                    "text_parts": [line.split(":", 1)[1].strip()],
                }
            continue
        if line.lower().startswith("question and answer"):
            flush_current()
            current_section = SECTION_QA
            continue

        colon_match = colon_pattern.match(line)
        if colon_match:
            flush_current()
            speaker = normalize_space(colon_match.group(1))
            text = normalize_space(colon_match.group(2))
            current = {
                "source_doc": source_doc,
                "section": current_section,
                "speaker": speaker,
                "speaker_role": _speaker_role_for(speaker, section=current_section),
                "speaker_title": "",
                "text_parts": [text] if text else [],
            }
            continue

        heading_match = heading_pattern.match(line)
        if heading_match:
            speaker = normalize_space(heading_match.group(1))
            title = normalize_space(heading_match.group(2))
            if speaker in MANAGEMENT_SPEAKERS or is_title_line(title):
                flush_current()
                current = {
                    "source_doc": source_doc,
                    "section": current_section,
                    "speaker": speaker,
                    "speaker_role": _speaker_role_for(speaker, section=current_section, title=title),
                    "speaker_title": title,
                    "text_parts": [],
                }
                continue

        if current is None:
            continue
        current["text_parts"].append(line)

    flush_current()
    return [block for block in blocks if block["speaker_role"] != "operator" or block["text"]]


def build_cleaned_transcript(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    last_section: str | None = None
    for block in blocks:
        if block["section"] != last_section:
            lines.append("Presentation" if block["section"] == SECTION_PRESENTATION else "Question and Answer")
            last_section = block["section"]
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
                    "source_doc": block["source_doc"],
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


def build_qa_pairs(blocks: list[dict[str, Any]], *, source_doc: str) -> list[dict[str, Any]]:
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
                        "source_doc": source_doc,
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
                "source_doc": source_doc,
                "qa_pair_id": pair_id,
                "question_speaker": current_question["speaker"],
                "question_text": current_question["text"],
                "answer_speakers": [item["speaker"] for item in current_answers],
                "answer_text": normalize_space(" ".join(item["text"] for item in current_answers)),
            }
        )
    return [pair for pair in qa_pairs if pair["question_text"]]


def normalize_paragraphs(text: str) -> list[str]:
    return [normalize_space(part) for part in re.split(r"\n\s*\n", text) if normalize_space(part)]


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


def compact_text_window(text: str, *, keywords: list[str], window_chars: int = 420) -> str:
    compact = normalize_space(text)
    lowered = compact.lower()
    for keyword in keywords:
        idx = lowered.find(keyword.lower())
        if idx != -1:
            start = max(0, idx - 120)
            end = min(len(compact), idx + window_chars)
            while start > 0 and compact[start - 1] != " ":
                start -= 1
            while end < len(compact) and compact[end] != " ":
                end += 1
            snippet = compact[start:end].strip()
            return extract_quote(snippet, max_chars=380)
    return extract_quote(compact, max_chars=380)


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


def _extract_release_metric(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.I)
    return match.group(1) if match else None


def build_results_release_evidence(text: str) -> dict[str, Any]:
    compact = normalize_space(text)
    revenue = _extract_release_metric(
        r"Revenue [–-] Revenue was \$([0-9.]+) billion,\s*a (?:decrease|decline) of [0-9]+%",
        compact,
    )
    revenue_down = _extract_release_metric(
        r"Revenue [–-] Revenue was \$[0-9.]+ billion,\s*a (?:decrease|decline) of ([0-9]+%)",
        compact,
    )
    op_income_match = re.search(
        r"Income from operations \$\s*([0-9,]+)\s+\$\s*[0-9,]+\s+\(([0-9]+)\)%",
        compact,
    )
    op_income = (
        f"{float(op_income_match.group(1).replace(',', '')) / 1000:.2f}"
        if op_income_match
        else None
    )
    op_income_down = f"{op_income_match.group(2)}%" if op_income_match else None
    margin_match = re.search(
        r"Operating margin\s+([0-9]+)\s*%\s+[0-9]+\s*%",
        compact,
    )
    operating_margin = f"{margin_match.group(1)}%" if margin_match else None
    eps_match = re.search(
        r"Diluted earnings per share \(EPS\)\s+\$\s*([0-9.]+)\s+\$\s*[0-9.]+\s+\(([0-9]+)\)%",
        compact,
    )
    eps = eps_match.group(1) if eps_match else None
    eps_down = f"{eps_match.group(2)}%" if eps_match else None
    expenses_2023 = _extract_release_metric(
        r"full-year 2023 total expenses will be in the range of \$([0-9\-]+ billion)",
        compact,
    )
    capex_2023 = _extract_release_metric(
        r"For 2023, we expect capital expenditures to be in the range of \$([0-9\-]+ billion)",
        compact,
    )
    q4_revenue_guide = _extract_release_metric(
        r"We expect fourth quarter 2022 total revenue to be in the range of \$([0-9\-.]+ billion)",
        compact,
    )
    evidence = {
        "headline_deterioration": compact_text_window(
            compact,
            keywords=["Revenue was $27.71 billion", "Income from operations was $5.66 billion"],
        ),
        "expense_guidance": compact_text_window(
            compact,
            keywords=["2023 total expenses", "96-101 billion"],
        ),
        "capex_guidance": compact_text_window(
            compact,
            keywords=["34-39 billion", "capital expenditures"],
        ),
        "efficiency_framing": compact_text_window(
            compact,
            keywords=["prioritization and efficiency", "headcount roughly flat"],
        ),
        "reality_labs_framing": compact_text_window(
            compact,
            keywords=["Reality Labs operating losses", "grow significantly"],
        ),
    }
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "quarter": EXPECTED_QUARTER,
        "event_date": EVENT_DATE,
        "metrics": {
            "revenue_billion_usd": revenue,
            "revenue_change_yoy": revenue_down,
            "operating_income_billion_usd": op_income,
            "operating_income_change_yoy": op_income_down,
            "operating_margin": operating_margin,
            "diluted_eps_usd": eps,
            "diluted_eps_change_yoy": eps_down,
            "q4_2022_revenue_guide_billion_usd": q4_revenue_guide,
            "expense_guidance_2023_billion_usd": expenses_2023,
            "capex_guidance_2023_billion_usd": capex_2023,
        },
        "evidence": evidence,
    }


def _last_numeric_value_after(label: str, compact: str, *, allow_negative: bool = False) -> str | None:
    idx = compact.lower().find(label.lower())
    if idx == -1:
        return None
    window = compact[idx : idx + 240]
    pattern = r"\(([0-9,]+)\)" if allow_negative else r"([0-9,]+%?)"
    matches = re.findall(pattern, window)
    return matches[-1] if matches else None


def _series_after(label: str, compact: str, *, pattern: str, window_chars: int = 240) -> list[str]:
    idx = compact.lower().find(label.lower())
    if idx == -1:
        return []
    window = compact[idx : idx + window_chars]
    return re.findall(pattern, window)


def build_presentation_support_metrics(text: str) -> dict[str, Any]:
    compact = normalize_space(text)
    reality_labs_match = re.search(r"Reality Labs Revenue ([0-9,\s]+?) Total Revenue", compact)
    total_revenue_match = re.search(r"Total Revenue \$ ([0-9,\s$]+?) Family of Apps Operating Income", compact)
    family_apps_match = re.search(
        r"Family of Apps Operating Income \$ ([0-9,\s$]+?) Reality Labs Operating \(Loss\)",
        compact,
    )
    reality_labs_loss_match = re.search(
        r"Reality Labs Operating \(Loss\) ([0-9,\s()]+?) Total Income from Operations",
        compact,
    )
    total_income_match = re.search(
        r"Total Income from Operations \$ ([0-9,\s$]+?) Operating Margin",
        compact,
    )
    margin_match = re.search(
        r"Operating Margin ([0-9%\s]+?) Beginning in the fourth quarter",
        compact,
    )
    reality_labs_revenue_series = re.findall(r"[0-9]{1,3}(?:,[0-9]{3})?", reality_labs_match.group(1)) if reality_labs_match else []
    total_revenue_series = re.findall(r"[0-9]{1,3}(?:,[0-9]{3})?", total_revenue_match.group(1)) if total_revenue_match else []
    family_apps_income_series = re.findall(r"[0-9]{1,3}(?:,[0-9]{3})?", family_apps_match.group(1)) if family_apps_match else []
    reality_labs_loss_series = re.findall(r"[0-9]{1,3}(?:,[0-9]{3})?", reality_labs_loss_match.group(1)) if reality_labs_loss_match else []
    total_income_series = re.findall(r"[0-9]{1,3}(?:,[0-9]{3})?", total_income_match.group(1)) if total_income_match else []
    operating_margin_series = re.findall(r"[0-9]{1,3}%", margin_match.group(1)) if margin_match else []
    capex_window = compact_text_window(compact, keywords=["Capital Expenditures", "9,518"], window_chars=320)
    capex_match = re.search(
        r"Capital Expenditures.*?\$([0-9,]+)\s+\$([0-9,]+)\s+\$([0-9,]+)\s+\$([0-9,]+)",
        compact,
    )
    capex_q3_2022 = capex_match.group(2) if capex_match else None
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "metrics": {
            "reality_labs_revenue_millions_usd": reality_labs_revenue_series[-1] if reality_labs_revenue_series else None,
            "total_revenue_millions_usd": total_revenue_series[-1] if total_revenue_series else None,
            "family_of_apps_operating_income_millions_usd": family_apps_income_series[-1] if family_apps_income_series else None,
            "reality_labs_operating_loss_millions_usd": reality_labs_loss_series[-1] if reality_labs_loss_series else None,
            "total_income_from_operations_millions_usd": total_income_series[-1] if total_income_series else None,
            "operating_margin": operating_margin_series[-1] if operating_margin_series else None,
            "q3_2022_capex_millions_usd": capex_q3_2022,
        },
        "evidence": {
            "segment_results": compact_text_window(
                compact,
                keywords=["Reality Labs Revenue", "Operating Margin"],
            ),
            "capital_expenditures": capex_window,
            "free_cash_flow_note": compact_text_window(
                compact,
                keywords=["Free Cash Flow Reconciliation", "non-GAAP"],
            ),
        },
    }


def build_financial_context_summary(
    results_release_evidence: dict[str, Any],
    presentation_support: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "quarter": EXPECTED_QUARTER,
        "official_results": results_release_evidence["metrics"],
        "presentation_support": presentation_support["metrics"],
        "summary_points": [
            "Revenue declined year-over-year while operating income, margin, and EPS deteriorated more sharply.",
            "2023 expense and capex guidance stayed elevated even as management emphasized efficiency and flatter headcount.",
            "Reality Labs remained a material drag on profitability in the presentation support deck.",
        ],
    }


def _qa_match_score(pair: dict[str, Any], *, question_keywords: list[str], answer_keywords: list[str]) -> int:
    question = normalize_space(pair.get("question_text", "")).lower()
    answer = normalize_space(pair.get("answer_text", "")).lower()
    score = 0
    for keyword in question_keywords:
        if keyword.lower() in question:
            score += 2
    for keyword in answer_keywords:
        if keyword.lower() in answer:
            score += 1
    return score


def select_audio_targets(qa_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    for spec in AUDIO_TARGET_SPECS:
        best_pair: dict[str, Any] | None = None
        best_score = 0
        for pair in qa_pairs:
            qa_pair_id = int(pair.get("qa_pair_id", -1))
            if qa_pair_id in used_ids:
                continue
            score = _qa_match_score(
                pair,
                question_keywords=spec["question_keywords"],
                answer_keywords=spec["answer_keywords"],
            )
            if score > best_score:
                best_score = score
                best_pair = pair
        if best_pair is not None and best_score >= 2:
            used_ids.add(int(best_pair["qa_pair_id"]))
            selected.append(
                {
                    "qa_pair_id": int(best_pair["qa_pair_id"]),
                    "row_id": spec["row_id"],
                    "plain_english_label": spec["plain_english_label"],
                    "review_priority": spec["review_priority"],
                    "why_it_matters": spec["why_it_matters"],
                    "question_keywords": spec["question_keywords"],
                    "answer_keywords": spec["answer_keywords"],
                }
            )
    return selected


def build_follow_up_pressure_signals(qa_pairs: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    specs = [
        {
            "row_id": "follow_up_reels_headwind_pressure",
            "label": "analyst follow-up on Reels headwind",
            "question_keywords": ["reels", "headwind"],
            "answer_keywords": ["500 million", "12 to 18 months", "neutral"],
            "why": "The follow-up call pushes management on how long the monetization headwind remains a real drag.",
        },
        {
            "row_id": "follow_up_macro_caution",
            "label": "management stayed cautious on macro",
            "question_keywords": ["macro", "playbook", "demand"],
            "answer_keywords": ["macro", "optimistic", "few more cards turned over"],
            "why": "This is the clearest follow-up moment where management refuses to sound fully confident on recovery timing.",
        },
        {
            "row_id": "follow_up_competition_ads",
            "label": "follow-up pressure on competition and ad demand",
            "question_keywords": ["competitive intensity", "demand environment"],
            "answer_keywords": ["post-att", "wide reach", "engagement"],
            "why": "This shows the follow-up transcript functioning as additional pressure testing rather than a separate narrative.",
        },
    ]
    for spec in specs:
        best_pair: dict[str, Any] | None = None
        best_score = 0
        for pair in qa_pairs:
            score = _qa_match_score(
                pair,
                question_keywords=spec["question_keywords"],
                answer_keywords=spec["answer_keywords"],
            )
            if score > best_score:
                best_score = score
                best_pair = pair
        if best_pair is None or best_score < 2:
            continue
        rows.append(
            {
                "row_id": spec["row_id"],
                "source": "follow_up_transcript",
                "qa_pair_id": int(best_pair["qa_pair_id"]),
                "question_speaker": best_pair["question_speaker"],
                "question_excerpt": extract_quote(best_pair["question_text"], max_chars=260),
                "answer_speakers": best_pair["answer_speakers"],
                "answer_excerpt": compact_text_window(
                    best_pair["answer_text"],
                    keywords=spec["answer_keywords"],
                    window_chars=260,
                ),
                "plain_english_label": spec["label"],
                "why_it_matters": spec["why"],
                "pressure_keywords_matched": best_score,
            }
        )
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "rows": rows,
    }


def _normalize_for_match(text: str) -> str:
    tokens = re.findall(r"[a-z0-9']+", text.lower())
    return " ".join(tokens)


def _excerpt_words(text: str, *, first_n: int | None = None, last_n: int | None = None) -> str:
    tokens = re.findall(r"\b[\w']+\b", normalize_space(text))
    if first_n is not None:
        tokens = tokens[:first_n]
    if last_n is not None:
        tokens = tokens[-last_n:]
    return " ".join(tokens)


def _best_window_match(
    segments: list[dict[str, Any]],
    target_text: str,
    *,
    after_index: int = 0,
    max_window: int = 8,
) -> dict[str, Any] | None:
    from difflib import SequenceMatcher

    target_norm = _normalize_for_match(target_text)
    if not target_norm:
        return None
    best: dict[str, Any] | None = None
    segment_count = len(segments)
    for start_idx in range(max(0, after_index), segment_count):
        parts: list[str] = []
        for end_idx in range(start_idx, min(segment_count, start_idx + max_window)):
            parts.append(str(segments[end_idx].get("text", "")))
            candidate_text = " ".join(parts)
            candidate_norm = _normalize_for_match(candidate_text)
            if not candidate_norm:
                continue
            score = SequenceMatcher(None, target_norm, candidate_norm).ratio()
            if best is None or score > best["score"]:
                best = {
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "start_s": float(segments[start_idx].get("start", 0.0)),
                    "end_s": float(segments[end_idx].get("end", 0.0)),
                    "score": round(float(score), 4),
                    "text": normalize_space(candidate_text),
                }
    return best


def _find_qa_pair(qa_pairs: list[dict[str, Any]], qa_pair_id: int) -> dict[str, Any] | None:
    for pair in qa_pairs:
        if int(pair.get("qa_pair_id", -1)) == qa_pair_id:
            return pair
    return None


def _count_restart_markers(text: str) -> int:
    lowered = normalize_space(text).lower()
    repeated_words = re.findall(r"\b([a-z']{2,})\b(?:[,\s]+\1\b)+", lowered)
    return lowered.count("...") + lowered.count("--") + len(repeated_words)


def _detect_hedge_markers(text: str) -> list[str]:
    lowered = normalize_space(text).lower()
    matches: list[str] = []
    for label, pattern in HEDGE_MARKER_PATTERNS:
        if pattern.search(lowered):
            matches.append(label)
    return matches


def _format_timestamp(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    total = max(0, int(round(float(seconds))))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _time_range_label(start_s: float | None, end_s: float | None) -> str | None:
    if start_s is None or end_s is None:
        return None
    return f"{_format_timestamp(start_s)}-{_format_timestamp(end_s)}"


def _audio_file_metadata(path: Path) -> dict[str, Any]:
    with wave.open(str(path), "rb") as handle:
        sample_rate = handle.getframerate()
        channels = handle.getnchannels()
        frame_count = handle.getnframes()
    duration_s = float(frame_count / sample_rate) if sample_rate else 0.0
    return {
        "duration_s": round(duration_s, 3),
        "sample_rate_hz": int(sample_rate),
        "channels": int(channels),
    }


def _ensure_audio_from_video(video_path: Path, audio_path: Path) -> dict[str, Any]:
    if audio_path.exists():
        metadata = _audio_file_metadata(audio_path)
        return {
            "status": "reused_existing_audio",
            "audio_path": str(audio_path),
            "audio_md5": md5_file(audio_path),
            **metadata,
        }
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not audio_path.exists():
        return {
            "status": "extraction_failed",
            "audio_path": str(audio_path),
            "error": ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip(),
        }
    metadata = _audio_file_metadata(audio_path)
    return {
        "status": "extracted_from_video",
        "audio_path": str(audio_path),
        "audio_md5": md5_file(audio_path),
        **metadata,
    }


def _load_or_build_audio_segments(
    *,
    audio_path: Path,
    output_path: Path,
    case_root: Path,
) -> list[dict[str, Any]]:
    audio_md5 = md5_file(audio_path)
    if output_path.exists():
        saved = json.loads(output_path.read_text(encoding="utf-8"))
        if saved.get("audio_md5") == audio_md5:
            return saved.get("segments", [])
    segments = transcribe_audio(
        str(audio_path),
        verbose=True,
        model_name="tiny",
        device="cpu",
        compute_type="int8",
        progress_log_interval_s=20.0,
    )
    payload = {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "audio_path": relative_to_case(audio_path, case_root),
        "audio_md5": audio_md5,
        "transcription_model": "tiny",
        "device": "cpu",
        "compute_type": "int8",
        "segments": segments,
    }
    write_json(output_path, payload)
    return segments


def _build_pair_shift_map(qa_shift_segments_path: Path) -> dict[int, dict[str, Any]]:
    if not qa_shift_segments_path.exists():
        return {}
    frame = pd.read_csv(qa_shift_segments_path)
    if frame.empty or "qa_pair_id" not in frame.columns:
        return {}
    result: dict[int, dict[str, Any]] = {}
    filtered = frame[frame["qa_pair_id"] > 0].copy()
    for qa_pair_id, group in filtered.groupby("qa_pair_id"):
        question_mean = group.loc[group["speaker_role"] == "analyst", "signed_score"].mean()
        answer_mean = group.loc[group["speaker_role"] == "management", "signed_score"].mean()
        if pd.isna(question_mean) or pd.isna(answer_mean):
            continue
        delta = float(answer_mean - question_mean)
        if delta <= -0.2:
            label = "weaker"
        elif delta >= 0.2:
            label = "stronger"
        else:
            label = "mixed"
        result[int(qa_pair_id)] = {
            "qa_shift_label": label,
            "answer_minus_question": round(delta, 4),
            "question_mean": round(float(question_mean), 4),
            "answer_mean": round(float(answer_mean), 4),
        }
    return result


def _build_curated_audio_alignment(
    *,
    qa_pairs: list[dict[str, Any]],
    audio_segments: list[dict[str, Any]],
    curated_targets: list[dict[str, Any]],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    matched_pairs: list[dict[str, Any]] = []
    cursor_idx = 0
    segment_id = 0
    for target in curated_targets:
        pair = _find_qa_pair(qa_pairs, target["qa_pair_id"])
        if pair is None:
            continue
        question_text = normalize_space(str(pair.get("question_text", "")))
        answer_text = normalize_space(str(pair.get("answer_text", "")))
        if not question_text or not answer_text:
            continue
        focused_question_text = compact_text_window(
            question_text,
            keywords=target.get("question_keywords", []),
            window_chars=220,
        )
        focused_answer_text = compact_text_window(
            answer_text,
            keywords=target.get("answer_keywords", []),
            window_chars=260,
        )
        question_start = _best_window_match(
            audio_segments,
            _excerpt_words(question_text, first_n=34),
            after_index=cursor_idx,
            max_window=4,
        )
        if question_start is None:
            continue
        question_end = _best_window_match(
            audio_segments,
            _excerpt_words(question_text, last_n=28),
            after_index=question_start["start_idx"],
            max_window=4,
        ) or question_start
        answer_start = _best_window_match(
            audio_segments,
            _excerpt_words(answer_text, first_n=38),
            after_index=question_end["end_idx"],
            max_window=5,
        )
        if answer_start is None:
            continue
        answer_end = _best_window_match(
            audio_segments,
            _excerpt_words(answer_text, last_n=34),
            after_index=answer_start["start_idx"],
            max_window=6,
        ) or answer_start

        question_duration = float(max(question_start["end_s"], question_end["end_s"]) - question_start["start_s"])
        answer_duration = float(max(answer_start["end_s"], answer_end["end_s"]) - answer_start["start_s"])
        answer_gap = float(answer_start["start_s"] - max(question_start["end_s"], question_end["end_s"]))
        if question_duration > 150.0 or answer_duration > 420.0 or answer_gap > 20.0:
            continue

        question_row = {
            "segment_id": segment_id,
            "start": round(float(question_start["start_s"]), 4),
            "end": round(float(max(question_start["end_s"], question_end["end_s"])), 4),
            "phase": "q_and_a",
            "speaker_role": "analyst",
            "qa_pair_id": int(pair["qa_pair_id"]),
            "text": focused_question_text,
        }
        segment_id += 1
        answer_row = {
            "segment_id": segment_id,
            "start": round(float(answer_start["start_s"]), 4),
            "end": round(float(max(answer_start["end_s"], answer_end["end_s"])), 4),
            "phase": "q_and_a",
            "speaker_role": "management",
            "qa_pair_id": int(pair["qa_pair_id"]),
            "text": focused_answer_text,
        }
        segment_id += 1
        rows.extend([question_row, answer_row])
        matched_pairs.append(
            {
                "qa_pair_id": int(pair["qa_pair_id"]),
                "row_id": target["row_id"],
                "plain_english_label": target["plain_english_label"],
                "review_priority": target["review_priority"],
                "why_it_matters": target["why_it_matters"],
                "question_speaker": pair.get("question_speaker"),
                "answer_speakers": pair.get("answer_speakers", []),
                "question_text": focused_question_text,
                "answer_text": focused_answer_text,
                "question_start_s": question_row["start"],
                "question_end_s": question_row["end"],
                "answer_start_s": answer_row["start"],
                "answer_end_s": answer_row["end"],
                "match_scores": {
                    "question_start": question_start["score"],
                    "question_end": question_end["score"],
                    "answer_start": answer_start["score"],
                    "answer_end": answer_end["score"],
                },
            }
        )
        cursor_idx = int(answer_end["end_idx"])
    return pd.DataFrame(rows), matched_pairs


def _plain_english_audio_summary(
    *,
    answer_start_delay_seconds: float | None,
    pause_before_answer_ms: float | None,
    filler_count: int,
    hesitation_label: str,
    hedge_markers: list[str],
) -> str:
    parts: list[str] = []
    if answer_start_delay_seconds is not None and answer_start_delay_seconds >= 1.5:
        parts.append("answer started more slowly")
    elif pause_before_answer_ms is not None and pause_before_answer_ms >= 650.0:
        parts.append("answer opened after a noticeable pause")
    if filler_count > 0:
        parts.append("used filler language")
    if hedge_markers:
        parts.append("opened with hedging or qualification")
    if hesitation_label in {"medium", "high"}:
        parts.append(f"overall hesitation scored {hesitation_label}")
    if not parts:
        parts.append("audio delivery stayed fairly direct")
    return "; ".join(parts)


def _build_audio_review_rows(
    *,
    case_root: Path,
    matched_pairs: list[dict[str, Any]],
    audio_behavior_segments_path: Path,
    qa_shift_map: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    if not audio_behavior_segments_path.exists():
        return []
    frame = pd.read_csv(audio_behavior_segments_path)
    frame = frame[frame["speaker_role"] == "management"].copy()
    review_rows: list[dict[str, Any]] = []
    for pair in matched_pairs:
        qa_pair_id = int(pair["qa_pair_id"])
        segment_row = frame.loc[frame["qa_pair_id"] == qa_pair_id]
        if segment_row.empty:
            continue
        row = segment_row.iloc[0]
        answer_start_delay_seconds = (
            round(float(row["answer_onset_delay_ms"]) / 1000.0, 2)
            if pd.notna(row["answer_onset_delay_ms"])
            else None
        )
        pause_before_answer_ms = (
            round(float(row["pause_before_answer_ms"]), 1)
            if pd.notna(row["pause_before_answer_ms"])
            else None
        )
        hedge_markers = _detect_hedge_markers(pair["answer_text"])
        qa_shift = qa_shift_map.get(qa_pair_id, {})
        plain_audio_summary = _plain_english_audio_summary(
            answer_start_delay_seconds=answer_start_delay_seconds,
            pause_before_answer_ms=pause_before_answer_ms,
            filler_count=int(row.get("filler_count", 0) or 0),
            hesitation_label=str(row.get("hesitation_label", "low")),
            hedge_markers=hedge_markers,
        )
        interpretation = "Analyst asked a direct question; "
        if answer_start_delay_seconds is not None and answer_start_delay_seconds >= 1.5:
            interpretation += "the answer started more slowly and "
        elif pause_before_answer_ms is not None and pause_before_answer_ms >= 650.0:
            interpretation += "there was a noticeable pause before the answer and "
        if hedge_markers:
            interpretation += "opened with hedging language. "
        else:
            interpretation += "stayed relatively direct in wording. "
        if qa_shift.get("qa_shift_label"):
            interpretation += f"Transcript-only Q&A shift stayed {qa_shift['qa_shift_label']}."
        review_rows.append(
            {
                "row_id": pair["row_id"],
                "qa_pair_id": qa_pair_id,
                "plain_english_label": pair["plain_english_label"],
                "review_priority": pair["review_priority"],
                "question_speaker": pair["question_speaker"],
                "answer_speakers": pair["answer_speakers"],
                "analyst_question_excerpt": extract_quote(pair["question_text"], max_chars=260),
                "management_answer_excerpt": extract_quote(pair["answer_text"], max_chars=320),
                "question_time_range": _time_range_label(pair["question_start_s"], pair["question_end_s"]),
                "answer_time_range": _time_range_label(pair["answer_start_s"], pair["answer_end_s"]),
                "question_start_s": pair["question_start_s"],
                "question_end_s": pair["question_end_s"],
                "answer_start_s": pair["answer_start_s"],
                "answer_end_s": pair["answer_end_s"],
                "answer_start_delay_seconds": answer_start_delay_seconds,
                "pause_before_answer_ms": pause_before_answer_ms,
                "filler_count": int(row.get("filler_count", 0) or 0),
                "filler_density": round(float(row.get("filler_density", 0.0) or 0.0), 4),
                "restart_count": _count_restart_markers(pair["answer_text"]),
                "transcript_hedge_markers": hedge_markers,
                "hesitation_score": int(row.get("hesitation_score", 0) or 0),
                "hesitation_label": str(row.get("hesitation_label", "low")),
                "hesitation_flag": str(row.get("hesitation_label", "low")) in {"medium", "high"},
                "qa_shift_label": qa_shift.get("qa_shift_label", "mixed"),
                "qa_shift_delta": qa_shift.get("answer_minus_question"),
                "plain_english_audio_summary": plain_audio_summary,
                "plain_english_interpretation": interpretation.strip(),
                "artifact_paths": [
                    "processed/qa_pairs/qa_pairs.json",
                    "processed/signals/qa_shift_summary.json",
                    "processed/audio_behavior/audio_behavior_segments.csv",
                    "processed/audio_behavior/audio_behavior_summary.json",
                ],
                "timing_note": AUDIO_ALIGNMENT_NOTE,
                "audio_support_mode": "supporting_only",
                "source_artifact_path": relative_to_case(audio_behavior_segments_path, case_root),
            }
        )
    return review_rows


def _rewrite_audio_summary_metadata_path(summary_path: Path, *, audio_path: Path, case_root: Path) -> None:
    if not summary_path.exists():
        return
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    metadata = payload.get("audio_metadata")
    if isinstance(metadata, dict):
        metadata["path"] = relative_to_case(audio_path, case_root)
    write_json(summary_path, payload)


def verify_video_media(video_path: Path, *, case_root: Path) -> dict[str, Any]:
    if not video_path.exists():
        return {
            "status": "missing",
            "expected_quarter": EXPECTED_QUARTER,
            "action": "Transcript-first build can proceed without media; optional audio hooks stay disabled.",
        }
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            str(video_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {
            "status": "error",
            "expected_quarter": EXPECTED_QUARTER,
            "video_filename": video_path.name,
            "action": "Media verification failed before optional audio hooks could run.",
            "error": ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip(),
        }
    output = proc.stdout or ""
    has_audio_stream = "codec_type=audio" in output
    has_video_stream = "codec_type=video" in output
    duration_match = re.search(r"duration=([0-9.]+)", output)
    return {
        "status": "verified" if has_audio_stream and has_video_stream else "partial",
        "expected_quarter": EXPECTED_QUARTER,
        "video_filename": video_path.name,
        "video_md5": md5_file(video_path),
        "source_video_path": str(video_path),
        "video_path": relative_to_case(video_path, case_root),
        "has_video_stream": has_video_stream,
        "has_audio_stream": has_audio_stream,
        "duration_s": round(float(duration_match.group(1)), 3) if duration_match else None,
        "verification_basis": [
            "asset path fixed to Meta Q3 2022 case",
            "ffprobe readable",
            "ffprobe audio stream present" if has_audio_stream else "ffprobe audio stream missing",
        ],
        "action": (
            "Quarter-consistent local video is readable and can be used for optional bounded audio hooks."
            if has_audio_stream and has_video_stream
            else "Media is readable but incomplete, so transcript-first outputs remain primary."
        ),
    }


def build_audio_status(
    *,
    paths: dict[str, Path],
    video_verification: dict[str, Any],
    case_root: Path,
    qa_pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    summary_path = paths["processed_audio_behavior"] / "audio_status.json"
    if video_verification.get("status") not in {"verified", "partial"} or not video_verification.get("has_audio_stream"):
        write_json(paths["processed_audio_behavior"] / "audio_review_rows.json", {"rows": []})
        write_json(paths["processed_joined_review"] / "joined_qa_audio_review.json", {"rows": []})
        status = {
            "status": "skipped",
            "reason": "No readable local video with an audio stream was available for optional bounded audio hooks.",
            "video_verification": {
                key: value for key, value in video_verification.items() if key != "source_video_path"
            },
            "expected_audio_target": "raw/audio/meta_q3_2022_audio.wav",
        }
        write_json(summary_path, status)
        return status

    raw_video = paths["raw_video"] / "meta_q3_2022_video.mp4"
    raw_audio = paths["raw_audio"] / "meta_q3_2022_audio.wav"
    extraction_status = _ensure_audio_from_video(raw_video, raw_audio)
    extraction_status["audio_path"] = relative_to_case(raw_audio, paths["case_root"])
    write_json(paths["processed_audio_behavior"] / "audio_extraction_status.json", extraction_status)
    if extraction_status.get("status") == "extraction_failed":
        write_json(paths["processed_audio_behavior"] / "audio_review_rows.json", {"rows": []})
        write_json(paths["processed_joined_review"] / "joined_qa_audio_review.json", {"rows": []})
        status = {
            "status": "error",
            "reason": "Video was readable, but extracting mono 16 kHz WAV audio failed.",
            "video_path": relative_to_case(raw_video, paths["case_root"]),
            "expected_audio_target": "raw/audio/meta_q3_2022_audio.wav",
            "audio_extraction_status": extraction_status,
            "video_verification": {
                key: value for key, value in video_verification.items() if key != "source_video_path"
            },
        }
        write_json(summary_path, status)
        return status

    curated_targets = select_audio_targets(qa_pairs)
    audio_segments_path = paths["processed_audio_behavior"] / "audio_transcript_segments.json"
    audio_segments = _load_or_build_audio_segments(
        audio_path=raw_audio,
        output_path=audio_segments_path,
        case_root=case_root,
    )
    aligned_df, matched_pairs = _build_curated_audio_alignment(
        qa_pairs=qa_pairs,
        audio_segments=audio_segments,
        curated_targets=curated_targets,
    )
    aligned_path = paths["processed_audio_behavior"] / "audio_aligned_qa_segments.csv"
    aligned_df.to_csv(aligned_path, index=False)
    if aligned_df.empty:
        write_json(paths["processed_audio_behavior"] / "audio_review_rows.json", {"rows": []})
        write_json(paths["processed_joined_review"] / "joined_qa_audio_review.json", {"rows": []})
        status = {
            "status": "partial",
            "reason": "Audio was extracted and transcribed, but curated Q&A timing matches were not strong enough for review rows.",
            "video_path": relative_to_case(raw_video, paths["case_root"]),
            "audio_path": relative_to_case(raw_audio, paths["case_root"]),
            "audio_extraction_status": extraction_status,
            "audio_transcript_segments_path": relative_to_case(audio_segments_path, paths["case_root"]),
            "audio_aligned_qa_segments_path": relative_to_case(aligned_path, paths["case_root"]),
            "timing_mode": "curated_qa_match_only",
            "timing_note": AUDIO_ALIGNMENT_NOTE,
            "video_verification": {
                key: value for key, value in video_verification.items() if key != "source_video_path"
            },
        }
        write_json(summary_path, status)
        return status

    audio_outputs = write_audio_behavior_outputs(
        raw_audio,
        aligned_df,
        paths["processed_audio_behavior"],
    )
    _rewrite_audio_summary_metadata_path(
        audio_outputs["summary_path"],
        audio_path=raw_audio,
        case_root=case_root,
    )
    qa_shift_map = _build_pair_shift_map(paths["processed_signals"] / "qa_shift_segments.csv")
    audio_review_rows = _build_audio_review_rows(
        case_root=case_root,
        matched_pairs=matched_pairs,
        audio_behavior_segments_path=audio_outputs["segments_path"],
        qa_shift_map=qa_shift_map,
    )
    write_json(paths["processed_audio_behavior"] / "audio_review_rows.json", {"rows": audio_review_rows})
    write_json(paths["processed_joined_review"] / "joined_qa_audio_review.json", {"rows": audio_review_rows})
    status = {
        "status": "generated",
        "reason": "Main-call video was readable, audio was extracted, and curated Q&A moments were matched to supporting audio.",
        "video_path": relative_to_case(raw_video, paths["case_root"]),
        "audio_path": relative_to_case(raw_audio, paths["case_root"]),
        "audio_extraction_status": extraction_status,
        "audio_transcript_segments_path": relative_to_case(audio_segments_path, paths["case_root"]),
        "audio_aligned_qa_segments_path": relative_to_case(aligned_path, paths["case_root"]),
        "audio_behavior_summary_path": relative_to_case(audio_outputs["summary_path"], paths["case_root"]),
        "audio_behavior_segments_path": relative_to_case(audio_outputs["segments_path"], paths["case_root"]),
        "audio_review_rows_path": "processed/audio_behavior/audio_review_rows.json",
        "joined_qa_audio_review_path": "processed/joined_review/joined_qa_audio_review.json",
        "usable_review_moments": len(audio_review_rows),
        "timing_mode": "curated_qa_match_only",
        "timing_note": AUDIO_ALIGNMENT_NOTE,
        "video_verification": {
            key: value for key, value in video_verification.items() if key != "source_video_path"
        },
    }
    write_json(summary_path, status)
    return status


def build_quarter_consistency(
    *,
    raw_assets: dict[str, Path],
    main_transcript_text: str,
    follow_up_text: str,
    results_release_text: str,
    presentation_text: str,
    video_verification: dict[str, Any],
) -> dict[str, Any]:
    transcript_status = "verified" if "Third Quarter 2022 Results Conference Call" in main_transcript_text else "unclear"
    follow_up_status = "verified" if "Third Quarter 2022 Follow Up Call" in follow_up_text else "unclear"
    results_status = "verified" if "Meta Reports Third Quarter 2022 Results" in results_release_text else "unclear"
    presentation_status = "verified" if "Meta Earnings Presentation Q3 2022" in presentation_text else "unclear"
    media_status = video_verification.get("status")
    overall_status = (
        "transcript_first_ready_media_available"
        if media_status == "verified"
        else "transcript_first_ready"
    )
    action_taken = (
        "Built the fixed Meta Q3 2022 transcript-first demo package from the earnings call transcript, follow-up transcript, "
        "results release, and presentation, with optional bounded audio support from a readable local Q3 video."
        if media_status == "verified"
        else "Built the fixed Meta Q3 2022 transcript-first demo package from the transcripts, results release, and presentation. "
        "Optional media support stayed limited or unavailable."
    )
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "expected_case_quarter": EXPECTED_QUARTER,
        "main_transcript": {
            "status": transcript_status,
            "detected_quarter": EXPECTED_QUARTER if transcript_status == "verified" else "unknown",
            "filename": raw_assets["transcript_pdf"].name,
            "supporting_text": "Meta Platforms, Inc. (META) Third Quarter 2022 Results Conference Call October 26th, 2022",
        },
        "follow_up_transcript": {
            "status": follow_up_status,
            "detected_quarter": EXPECTED_QUARTER if follow_up_status == "verified" else "unknown",
            "filename": raw_assets["follow_up_pdf"].name,
            "supporting_text": "Meta Platforms, Inc. (META) Third Quarter 2022 Follow Up Call October 26th, 2022",
        },
        "results_release": {
            "status": results_status,
            "detected_quarter": EXPECTED_QUARTER if results_status == "verified" else "unknown",
            "filename": raw_assets["results_release_pdf"].name,
            "supporting_text": "Meta Reports Third Quarter 2022 Results",
        },
        "presentation": {
            "status": presentation_status,
            "detected_quarter": EXPECTED_QUARTER if presentation_status == "verified" else "unknown",
            "filename": raw_assets["presentation_pdf"].name,
            "supporting_text": "Meta Earnings Presentation Q3 2022",
        },
        "video": {
            key: value for key, value in video_verification.items() if key != "source_video_path"
        },
        "overall_status": overall_status,
        "action_taken": action_taken,
    }


def build_market_context_artifact() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "company": "Meta Platforms",
        "ticker": "META",
        "quarter": EXPECTED_QUARTER,
        "event_date": EVENT_DATE,
        "key_extracted_signals": [
            "revenue down 4%",
            "operating margin down to 20%",
            "2023 expense guidance remained elevated despite efficiency framing",
            "Reels still carried a more than $500 million quarterly revenue headwind",
        ],
        "market_reaction_window": {
            "start_date": "2022-10-26",
            "end_date": "2022-10-27",
            "reaction_direction": "negative",
            "reaction_magnitude_pct": -24.6,
            "start_price_usd": 129.82,
            "end_price_usd": 97.94,
        },
        "market_reaction_note": (
            "Meta fell sharply the session after the release as investors reacted to weaker profitability, "
            "heavy 2023 spending expectations, and the lack of a cleaner near-term recovery story."
        ),
        "source": {
            "label": "Stooq daily META prices and CNBC coverage of Meta's Oct. 27, 2022 selloff",
            "pricing_url": "https://stooq.com/q/d/l/?s=meta.us&i=d",
            "coverage_url": "https://www.cnbc.com/2022/10/27/meta-stock-plunges-on-earnings-miss-weak-fourth-quarter-forecast.html",
        },
        "caveat": (
            "Contextual sanity-check evidence only. This does not validate prediction, causality, or trading value."
        ),
    }


def build_evidence_rows(
    *,
    case_root: Path,
    main_blocks: list[dict[str, Any]],
    follow_up_pressure_signals: dict[str, Any],
    release_evidence: dict[str, Any],
    presentation_support: dict[str, Any],
    audio_review_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    macro_block = find_block(
        main_blocks,
        keywords=["volatile macroeconomy", "ads signal loss", "growing costs"],
        speaker="Mark Zuckerberg",
    )
    if macro_block:
        rows.append(
            {
                "row_id": "transcript_macro_ads_pressure",
                "source_type": "transcript",
                "source": "transcript",
                "source_section_or_speaker": "Mark Zuckerberg / prepared remarks",
                "speaker": macro_block["speaker"],
                "speaker_role": macro_block["speaker_role"],
                "source_excerpt": compact_text_window(
                    macro_block["text"],
                    keywords=["volatile macroeconomy", "ads signal loss", "growing costs"],
                    window_chars=260,
                ),
                "raw_excerpt": compact_text_window(
                    macro_block["text"],
                    keywords=["volatile macroeconomy", "ads signal loss", "growing costs"],
                    window_chars=260,
                ),
                "source_artifact_path": "processed/transcript_text/transcript_cleaned.txt",
                "source_locator": f"block_id:{macro_block['block_id']}",
                "extracted_signal": "management explicitly flagged macro pressure, competition, ads signal loss, and higher investment costs",
                "plain_english_label": "management flagged macro and ads pressure",
                "why_it_matters": "This is the cleanest transcript-first statement of why the quarter felt pressured before the Q&A begins.",
                "ambiguity_note": "The pressure is explicit, but the exact timing of recovery is still left open.",
                "review_priority": "high",
                "optional_audio_support": None,
                "optional_timestamp": None,
            }
        )

    conservative_block = find_block(
        main_blocks,
        keywords=["not clear that the economy has stabilized", "budget somewhat more conservatively"],
        speaker="Mark Zuckerberg",
    )
    if conservative_block:
        capex_audio = next((row for row in audio_review_rows if row["row_id"] == "qa_efficiency_spending_audio"), None)
        rows.append(
            {
                "row_id": "transcript_conservative_budget",
                "source_type": "transcript",
                "source": "transcript",
                "source_section_or_speaker": "Mark Zuckerberg / prepared remarks",
                "speaker": conservative_block["speaker"],
                "speaker_role": conservative_block["speaker_role"],
                "source_excerpt": compact_text_window(
                    conservative_block["text"],
                    keywords=["not clear that the economy has stabilized", "budget somewhat more conservatively"],
                    window_chars=260,
                ),
                "raw_excerpt": compact_text_window(
                    conservative_block["text"],
                    keywords=["not clear that the economy has stabilized", "budget somewhat more conservatively"],
                    window_chars=260,
                ),
                "source_artifact_path": "processed/transcript_text/transcript_cleaned.txt",
                "source_locator": f"block_id:{conservative_block['block_id']}",
                "extracted_signal": "management coupled cautious macro language with a flatter 2023 organization plan",
                "plain_english_label": "management turned more cautious on 2023 spending",
                "why_it_matters": "This is the transcript-first bridge between efficiency language and still-heavy investment commitments elsewhere in the package.",
                "ambiguity_note": "This signals caution and discipline, but it does not resolve whether the spending plan is enough to restore profitability quickly.",
                "review_priority": "high",
                "optional_audio_support": capex_audio,
                "optional_timestamp": capex_audio.get("answer_time_range") if capex_audio else None,
            }
        )

    reels_block = find_block(
        main_blocks,
        keywords=["500 million quarterly revenue headwind", "12-18 months"],
        speaker="Mark Zuckerberg",
    )
    if reels_block:
        reels_audio = next((row for row in audio_review_rows if row["row_id"] == "qa_reels_headwind_audio"), None)
        rows.append(
            {
                "row_id": "transcript_reels_headwind",
                "source_type": "transcript",
                "source": "transcript",
                "source_section_or_speaker": "Mark Zuckerberg / prepared remarks",
                "speaker": reels_block["speaker"],
                "speaker_role": reels_block["speaker_role"],
                "source_excerpt": compact_text_window(
                    reels_block["text"],
                    keywords=["500 million quarterly revenue headwind", "12-18 months"],
                    window_chars=260,
                ),
                "raw_excerpt": compact_text_window(
                    reels_block["text"],
                    keywords=["500 million quarterly revenue headwind", "12-18 months"],
                    window_chars=260,
                ),
                "source_artifact_path": "processed/transcript_text/transcript_cleaned.txt",
                "source_locator": f"block_id:{reels_block['block_id']}",
                "extracted_signal": "Reels remained a material monetization headwind, with neutrality still 12-18 months away",
                "plain_english_label": "Reels monetization remained a clear headwind",
                "why_it_matters": "This is one of the strongest product-to-financial bridge moments in the case and it stays explicitly qualified.",
                "ambiguity_note": "Management gives a direction of travel, but the timing to a neutral or positive contribution stays qualified.",
                "review_priority": "high",
                "optional_audio_support": reels_audio,
                "optional_timestamp": reels_audio.get("answer_time_range") if reels_audio else None,
            }
        )

    rows.append(
        {
            "row_id": "release_profitability_deterioration",
            "source_type": "results_release",
            "source": "results_release",
            "source_section_or_speaker": "Meta Q3 2022 results release",
            "speaker": "Meta results release",
            "speaker_role": "management_document",
            "source_excerpt": release_evidence["evidence"]["headline_deterioration"],
            "raw_excerpt": release_evidence["evidence"]["headline_deterioration"],
            "source_artifact_path": "processed/signals/results_release_evidence.json",
            "source_locator": "headline_deterioration",
            "extracted_signal": "official disclosure shows revenue down 4%, operating income down 46%, operating margin down to 20%, and EPS down sharply",
            "plain_english_label": "profitability deteriorated sharply",
            "why_it_matters": "This is the cleanest official anchor for why the rest of the transcript and Q&A felt defensive.",
            "ambiguity_note": "These are disclosed results, not an interpretation of tone or delivery.",
            "review_priority": "high",
            "optional_audio_support": None,
            "optional_timestamp": None,
        }
    )

    capex_audio = next((row for row in audio_review_rows if row["row_id"] == "qa_capex_ai_pressure_audio"), None)
    rows.append(
        {
            "row_id": "release_expense_capex_guidance",
            "source_type": "results_release",
            "source": "results_release",
            "source_section_or_speaker": "Meta Q3 2022 results release",
            "speaker": "Meta results release",
            "speaker_role": "management_document",
            "source_excerpt": release_evidence["evidence"]["capex_guidance"],
            "raw_excerpt": release_evidence["evidence"]["expense_guidance"],
            "source_artifact_path": "processed/signals/results_release_evidence.json",
            "source_locator": "expense_guidance + capex_guidance",
            "extracted_signal": "2023 expense guidance stayed elevated and capex guidance rose to $34-39 billion, driven mainly by AI capacity",
            "plain_english_label": "efficiency language still came with heavy spending",
            "why_it_matters": "This is the strongest official disclosure row for the tension between cost discipline messaging and continued investment intensity.",
            "ambiguity_note": "Management gives ranges and priorities, but not a short clean path back to prior margins.",
            "review_priority": "high",
            "optional_audio_support": capex_audio,
            "optional_timestamp": capex_audio.get("answer_time_range") if capex_audio else None,
        }
    )

    rows.append(
        {
            "row_id": "presentation_reality_labs_drag",
            "source_type": "presentation",
            "source": "presentation",
            "source_section_or_speaker": "Meta Q3 2022 earnings presentation",
            "speaker": "Meta earnings presentation",
            "speaker_role": "management_document",
            "source_excerpt": presentation_support["evidence"]["segment_results"],
            "raw_excerpt": presentation_support["evidence"]["segment_results"],
            "source_artifact_path": "processed/signals/presentation_support_metrics.json",
            "source_locator": "segment_results",
            "extracted_signal": "Reality Labs revenue stayed small while operating losses remained large relative to total operating income",
            "plain_english_label": "Reality Labs remained a major drag on profits",
            "why_it_matters": "The deck makes the profitability drag visually concrete in a way the transcript alone does not.",
            "ambiguity_note": "This row shows the size of the drag, not whether the investment strategy is ultimately right or wrong.",
            "review_priority": "high",
            "optional_audio_support": None,
            "optional_timestamp": None,
        }
    )

    follow_up_rows = follow_up_pressure_signals.get("rows", [])
    if follow_up_rows:
        primary_follow_up = follow_up_rows[0]
        rows.append(
            {
                "row_id": primary_follow_up["row_id"],
                "source_type": "follow_up_transcript",
                "source": "follow_up_transcript",
                "source_section_or_speaker": f"{primary_follow_up['question_speaker']} / follow-up Q&A",
                "speaker": primary_follow_up["question_speaker"],
                "speaker_role": "analyst",
                "source_excerpt": primary_follow_up["answer_excerpt"],
                "raw_excerpt": primary_follow_up["question_excerpt"],
                "source_artifact_path": "processed/signals/follow_up_pressure_signals.json",
                "source_locator": f"qa_pair_id:{primary_follow_up['qa_pair_id']}",
                "extracted_signal": primary_follow_up["plain_english_label"],
                "plain_english_label": "analyst kept pressure on the weak spots",
                "why_it_matters": primary_follow_up["why_it_matters"],
                "ambiguity_note": "This comes from the same day follow-up call and functions as added pressure-testing context rather than the canonical spoken source.",
                "review_priority": "high",
                "optional_audio_support": None,
                "optional_timestamp": None,
            }
        )
    if len(follow_up_rows) > 1:
        cautious_follow_up = follow_up_rows[1]
        rows.append(
            {
                "row_id": cautious_follow_up["row_id"],
                "source_type": "follow_up_transcript",
                "source": "follow_up_transcript",
                "source_section_or_speaker": f"{cautious_follow_up['question_speaker']} / follow-up Q&A",
                "speaker": ", ".join(cautious_follow_up["answer_speakers"]),
                "speaker_role": "management",
                "source_excerpt": cautious_follow_up["answer_excerpt"],
                "raw_excerpt": cautious_follow_up["answer_excerpt"],
                "source_artifact_path": "processed/signals/follow_up_pressure_signals.json",
                "source_locator": f"qa_pair_id:{cautious_follow_up['qa_pair_id']}",
                "extracted_signal": cautious_follow_up["plain_english_label"],
                "plain_english_label": "management stayed cautious on the recovery story",
                "why_it_matters": cautious_follow_up["why_it_matters"],
                "ambiguity_note": "This is cautious language rather than an explicit reversal in guidance or strategy.",
                "review_priority": "high",
                "optional_audio_support": None,
                "optional_timestamp": None,
            }
        )

    return rows[:8]


def build_joined_review_moments(
    evidence_rows: list[dict[str, Any]],
    audio_review_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in evidence_rows:
        joined = dict(row)
        joined["moment_type"] = "side_by_side_review"
        joined["transcript_first"] = True
        if row.get("optional_audio_support"):
            joined["audio_support"] = row["optional_audio_support"]
            selected.append(joined)
    return selected[:3]


def build_demo_summary(
    *,
    case_root: Path,
    quarter_consistency: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    qa_pairs: list[dict[str, Any]],
    follow_up_qa_pairs: list[dict[str, Any]],
    audio_status: dict[str, Any],
    market_context: dict[str, Any],
) -> dict[str, Any]:
    signals_dir = case_root / "processed" / "signals"
    metrics = json.loads((signals_dir / "metrics.json").read_text(encoding="utf-8"))
    guidance_df = read_csv_or_empty(signals_dir / "guidance.csv")
    uncertainty_df = read_csv_or_empty(signals_dir / "uncertainty_signals.csv")
    skepticism_df = read_csv_or_empty(signals_dir / "analyst_skepticism.csv")
    return {
        "schema_version": "1.0.0",
        "case_id": CASE_ID,
        "display_name": CASE_LABEL,
        "quarter": EXPECTED_QUARTER,
        "quarter_consistency": quarter_consistency,
        "transcript_first_status": "ready",
        "audio_status": audio_status,
        "headline_counts": {
            "guidance_rows": int(len(guidance_df)),
            "uncertainty_rows": int(len(uncertainty_df)),
            "analyst_skepticism_rows": int(len(skepticism_df)),
            "main_qa_pairs": int(len(qa_pairs)),
            "follow_up_qa_pairs": int(len(follow_up_qa_pairs)),
            "evidence_rows": int(len(evidence_rows)),
            "audio_review_moments": int(audio_status.get("usable_review_moments", 0)),
        },
        "review_scorecard": metrics.get("review_scorecard", {}),
        "market_context": market_context,
        "top_summary_points": [
            "The main earnings call transcript, follow-up transcript, results release, and presentation are quarter-consistent for Meta Q3 2022.",
            "The transcript-first package surfaces macro pressure, Reels monetization headwinds, cost discipline language, and Reality Labs drag.",
            "The follow-up transcript adds extra analyst pressure on weak spots without replacing the main call as the canonical spoken source.",
            "Optional audio support is limited to a few curated main-call Q&A moments and remains supporting context only.",
        ],
        "limitations": [
            "This is a transcript-first deterministic review package, not a predictive or trading system.",
            "Audio and video are supporting layers only; they do not override transcript-first extracted signals.",
            AUDIO_ALIGNMENT_NOTE,
            "Market reaction context is a historical sanity-check panel, not predictive validation or a trading claim.",
        ],
    }


def build_fixture(
    *,
    quarter_consistency: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    audio_status: dict[str, Any],
    market_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "display_name": CASE_LABEL,
        "quarter": EXPECTED_QUARTER,
        "case_status": summary["quarter_consistency"]["overall_status"],
        "quarter_consistency": quarter_consistency,
        "artifact_paths": {
            "transcript_cleaned": "processed/transcript_text/transcript_cleaned.txt",
            "transcript_sectioned": "processed/transcript_text/transcript_sectioned.json",
            "follow_up_cleaned": "processed/follow_up_text/follow_up_cleaned.txt",
            "follow_up_sectioned": "processed/follow_up_text/follow_up_sectioned.json",
            "qa_pairs": "processed/qa_pairs/qa_pairs.json",
            "follow_up_qa_pairs": "processed/qa_pairs/follow_up_qa_pairs.json",
            "guidance": "processed/signals/guidance.csv",
            "uncertainty": "processed/signals/uncertainty_signals.csv",
            "qa_shift_summary": "processed/signals/qa_shift_summary.json",
            "results_release_evidence": "processed/signals/results_release_evidence.json",
            "presentation_support_metrics": "processed/signals/presentation_support_metrics.json",
            "financial_context_summary": "processed/signals/financial_context_summary.json",
            "follow_up_pressure_signals": "processed/signals/follow_up_pressure_signals.json",
            "audio_status": "processed/audio_behavior/audio_status.json",
            "audio_transcript_segments": "processed/audio_behavior/audio_transcript_segments.json",
            "audio_aligned_qa_segments": "processed/audio_behavior/audio_aligned_qa_segments.csv",
            "audio_behavior_summary": "processed/audio_behavior/audio_behavior_summary.json",
            "audio_behavior_segments": "processed/audio_behavior/audio_behavior_segments.csv",
            "audio_review_rows": "processed/audio_behavior/audio_review_rows.json",
            "joined_qa_audio_review": "processed/joined_review/joined_qa_audio_review.json",
            "quarter_consistency": "processed/joined_review/quarter_consistency.json",
            "joined_review_moments": "processed/joined_review/joined_review_moments.json",
            "market_context": "demo/summary/meta_q3_2022_market_context.json",
            "evidence_rows": "demo/evidence_rows/meta_q3_2022_evidence_rows.json",
            "summary": "demo/summary/meta_q3_2022_summary.json",
        },
        "evidence_rows_preview": evidence_rows[:6],
        "audio_status": audio_status,
        "market_context": market_context,
        "notes": [
            "Main-call transcript-first artifacts are the source of truth for this demo case.",
            "The follow-up transcript is additional analyst-pressure context and does not replace the main call.",
            "Later UI work can consume this fixture directly without running the full live pipeline.",
        ],
    }


def build_demo_case(*, case_root: Path) -> dict[str, Path]:
    paths = ensure_scaffold(case_root)
    raw_assets = expected_raw_assets(paths)
    missing = [str(path) for key, path in raw_assets.items() if key != "audio_path" and key != "video_path" and not path.exists()]
    if raw_assets["video_path"].exists():
        pass
    if missing:
        raise RuntimeError(
            "Meta demo raw assets are missing. Expected: " + ", ".join(missing)
        )

    main_pages = extract_pdf_pages(raw_assets["transcript_pdf"])
    follow_up_pages = extract_pdf_pages(raw_assets["follow_up_pdf"])
    results_release_text = extract_pdf_text(raw_assets["results_release_pdf"])
    presentation_text = extract_pdf_text(raw_assets["presentation_pdf"])

    main_raw_text = "\n\n".join(f"=== PAGE {i + 1} ===\n{page}" for i, page in enumerate(main_pages))
    follow_up_raw_text = "\n\n".join(f"=== PAGE {i + 1} ===\n{page}" for i, page in enumerate(follow_up_pages))

    main_lines = clean_main_transcript_pages(main_pages)
    follow_up_lines = clean_follow_up_pages(follow_up_pages)
    main_blocks = build_speaker_blocks(main_lines, source_doc="main_transcript")
    follow_up_blocks = build_speaker_blocks(follow_up_lines, source_doc="follow_up_transcript")
    main_cleaned = build_cleaned_transcript(main_blocks)
    follow_up_cleaned = build_cleaned_transcript(follow_up_blocks)

    main_segments, main_segment_metadata = build_synthetic_segments(main_blocks)
    follow_up_segments, follow_up_segment_metadata = build_synthetic_segments(follow_up_blocks)
    qa_pairs = build_qa_pairs(main_blocks, source_doc="main_transcript")
    follow_up_qa_pairs = build_qa_pairs(follow_up_blocks, source_doc="follow_up_transcript")

    transcript_dir = paths["processed_transcript"]
    follow_up_dir = paths["processed_follow_up"]
    (transcript_dir / "transcript_raw_extract.txt").write_text(main_raw_text, encoding="utf-8")
    (transcript_dir / "transcript_cleaned.txt").write_text(main_cleaned, encoding="utf-8")
    write_json(transcript_dir / "transcript_sectioned.json", {"blocks": main_blocks})
    write_transcript_artifacts(main_segments, transcript_dir)

    (follow_up_dir / "follow_up_raw_extract.txt").write_text(follow_up_raw_text, encoding="utf-8")
    (follow_up_dir / "follow_up_cleaned.txt").write_text(follow_up_cleaned, encoding="utf-8")
    write_json(follow_up_dir / "follow_up_sectioned.json", {"blocks": follow_up_blocks})
    write_transcript_artifacts(follow_up_segments, follow_up_dir)

    write_json(paths["processed_qa_pairs"] / "qa_pairs.json", {"qa_pairs": qa_pairs})
    write_json(paths["processed_qa_pairs"] / "follow_up_qa_pairs.json", {"qa_pairs": follow_up_qa_pairs})
    write_json(paths["processed_chunks"] / "segment_metadata.json", {"segments": main_segment_metadata})
    write_json(paths["processed_chunks"] / "follow_up_segment_metadata.json", {"segments": follow_up_segment_metadata})

    release_evidence = build_results_release_evidence(results_release_text)
    presentation_support = build_presentation_support_metrics(presentation_text)
    financial_context = build_financial_context_summary(release_evidence, presentation_support)
    follow_up_pressure_signals = build_follow_up_pressure_signals(follow_up_qa_pairs)

    signals_dir = paths["processed_signals"]
    artifacts = write_sentiment_artifacts(
        segments=main_segments,
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
    (signals_dir / "results_release_text.txt").write_text(results_release_text, encoding="utf-8")
    (signals_dir / "presentation_text.txt").write_text(presentation_text, encoding="utf-8")
    write_json(signals_dir / "results_release_evidence.json", release_evidence)
    write_json(signals_dir / "presentation_support_metrics.json", presentation_support)
    write_json(signals_dir / "financial_context_summary.json", financial_context)
    write_json(signals_dir / "follow_up_pressure_signals.json", follow_up_pressure_signals)

    video_verification = verify_video_media(raw_assets["video_path"], case_root=case_root)
    write_json(
        paths["raw_video"] / "video_verification.json",
        {key: value for key, value in video_verification.items() if key != "source_video_path"},
    )

    audio_status = build_audio_status(
        paths=paths,
        video_verification=video_verification,
        case_root=case_root,
        qa_pairs=qa_pairs,
    )

    quarter_consistency = build_quarter_consistency(
        raw_assets=raw_assets,
        main_transcript_text=extract_pdf_text(raw_assets["transcript_pdf"]),
        follow_up_text=extract_pdf_text(raw_assets["follow_up_pdf"]),
        results_release_text=results_release_text,
        presentation_text=presentation_text,
        video_verification=video_verification,
    )
    write_json(paths["processed_joined_review"] / "quarter_consistency.json", quarter_consistency)

    audio_review_payload = load_json_if_exists(paths["processed_audio_behavior"] / "audio_review_rows.json")
    audio_review_rows = audio_review_payload.get("rows", []) if audio_review_payload else []

    evidence_rows = build_evidence_rows(
        case_root=case_root,
        main_blocks=main_blocks,
        follow_up_pressure_signals=follow_up_pressure_signals,
        release_evidence=release_evidence,
        presentation_support=presentation_support,
        audio_review_rows=audio_review_rows,
    )
    market_context = build_market_context_artifact()
    summary = build_demo_summary(
        case_root=case_root,
        quarter_consistency=quarter_consistency,
        evidence_rows=evidence_rows,
        qa_pairs=qa_pairs,
        follow_up_qa_pairs=follow_up_qa_pairs,
        audio_status=audio_status,
        market_context=market_context,
    )
    fixture = build_fixture(
        quarter_consistency=quarter_consistency,
        evidence_rows=evidence_rows,
        summary=summary,
        audio_status=audio_status,
        market_context=market_context,
    )
    joined_review = {
        "case_id": CASE_ID,
        "joined_review_moments": build_joined_review_moments(evidence_rows, audio_review_rows),
        "audio_status": audio_status,
        "market_context_path": "demo/summary/meta_q3_2022_market_context.json",
    }

    write_json(paths["processed_joined_review"] / "joined_review_moments.json", joined_review)
    if not (paths["processed_joined_review"] / "joined_qa_audio_review.json").exists():
        write_json(paths["processed_joined_review"] / "joined_qa_audio_review.json", {"rows": []})
    if not (paths["processed_audio_behavior"] / "audio_status.json").exists():
        write_json(paths["processed_audio_behavior"] / "audio_status.json", audio_status)
    write_json(paths["demo_evidence"] / "meta_q3_2022_evidence_rows.json", {"rows": evidence_rows})
    write_json(paths["demo_evidence"] / "meta_demo_evidence_rows.json", {"rows": evidence_rows})
    write_json(paths["demo_summary"] / "meta_q3_2022_market_context.json", market_context)
    write_json(paths["demo_summary"] / "meta_q3_2022_summary.json", summary)
    write_json(paths["demo_summary"] / "meta_demo_summary.json", summary)
    write_json(paths["demo_fixtures"] / "meta_q3_2022_fixture.json", fixture)
    write_json(paths["demo_fixtures"] / "meta_demo_fixture.json", fixture)

    return {
        "quarter_consistency_path": paths["processed_joined_review"] / "quarter_consistency.json",
        "evidence_rows_path": paths["demo_evidence"] / "meta_q3_2022_evidence_rows.json",
        "summary_path": paths["demo_summary"] / "meta_q3_2022_summary.json",
        "fixture_path": paths["demo_fixtures"] / "meta_q3_2022_fixture.json",
        "audio_status_path": paths["processed_audio_behavior"] / "audio_status.json",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the fixed Meta Q3 2022 transcript-first demo case bundle from repo-local raw assets. "
            "The script generates deterministic transcript-first artifacts, follow-up-call pressure context, "
            "and optional bounded audio hooks when the local video is readable."
        )
    )
    parser.add_argument(
        "--case-root",
        type=Path,
        default=Path("data/demo_cases/meta_q3_2022"),
        help="Repo-local case root for the fixed Meta demo package.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    case_root = args.case_root.expanduser().resolve()
    outputs = build_demo_case(case_root=case_root)
    print(f"Meta demo case built at: {case_root}")
    print(f"Quarter consistency: {outputs['quarter_consistency_path']}")
    print(f"Evidence rows: {outputs['evidence_rows_path']}")
    print(f"Summary: {outputs['summary_path']}")
    print(f"Fixture: {outputs['fixture_path']}")
    print(f"Audio status: {outputs['audio_status_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
