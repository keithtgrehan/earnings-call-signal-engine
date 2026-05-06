from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "data" / "gold" / "gold_labels.jsonl"
MANIFEST_PATH = ROOT / "data" / "corpus" / "manifests" / "pilot_corpus_manifest.csv"
PACKET_CSV = ROOT / "data" / "labeling" / "priority_review_packet.csv"
PACKET_MD = ROOT / "data" / "labeling" / "priority_review_packet.md"
LABELS = ("risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral")

PRIORITY_1_CALLS: tuple[dict[str, str], ...] = (
    {"requested_case_id": "NVDA_2026_Q4", "case_id": "NVDA_2026_Q4_call07", "ticker": "NVDA", "fiscal_period": "Q4_2026"},
    {"requested_case_id": "META_2025_Q4", "case_id": "META_2025_Q4", "ticker": "META", "fiscal_period": "Q4_2025"},
    {"requested_case_id": "AMZN_2025_Q4", "case_id": "AMZN_2025_Q4_watchhold01", "ticker": "AMZN", "fiscal_period": "Q4_2025"},
    {"requested_case_id": "AAPL_2026_Q1", "case_id": "AAPL_2026_Q1_call06", "ticker": "AAPL", "fiscal_period": "Q1_2026"},
    {"requested_case_id": "MSFT_2026_Q1", "case_id": "MSFT_2026_Q1_holdout04", "ticker": "MSFT", "fiscal_period": "Q1_2026"},
    {"requested_case_id": "GOOGL_2025_Q4_call03", "case_id": "GOOGL_2025_Q4_call03", "ticker": "GOOGL", "fiscal_period": "Q4_2025"},
    {"requested_case_id": "PLTR_2025_Q4_call01", "case_id": "PLTR_2025_Q4_call01", "ticker": "PLTR", "fiscal_period": "Q4_2025"},
)

PRIORITY_2_TICKERS: tuple[str, ...] = (
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

REVIEW_FIELDS = (
    "review_id",
    "case_id",
    "ticker",
    "fiscal_period",
    "source_path",
    "section",
    "speaker",
    "evidence_text",
    "predicted_label",
    "alternative_label_if_ambiguous",
    "trigger_terms",
    "deterministic_confidence",
    "ml_prediction_if_available",
    "disagreement_flag",
    "review_priority_reason",
    "reviewer_decision",
    "corrected_label",
    "reviewer_notes",
)

GUIDANCE_RE = re.compile(r"\b(guidance|outlook|expect|expected|forecast|revenue|eps|margin|plus or minus|raised|lowered)\b", re.I)
PRESSURE_RE = re.compile(r"\b(analyst|question|concern|pressure|why|how should|can you|what gives|confidence)\b", re.I)
UNCERTAINTY_RE = re.compile(r"\b(if|whether|could|may|might|probably|unclear|depends|assuming|subject to|once)\b", re.I)
NEUTRAL_STATUS_RE = re.compile(r"\b(status|scheduled|agenda|meeting|open|legal review|renewal review|for reference)\b", re.I)
FALSE_POSITIVE_RE = re.compile(r"\b(send|pilot|procurement|rollout|security review|expansion|renewal|legal|still open)\b", re.I)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: tuple[str, ...] = REVIEW_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def row_label(row: dict[str, Any]) -> str:
    return str(row.get("signal_family") or row.get("label") or "").strip()


def row_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("evidence_text") or row.get("matched_text") or "").strip()


def gold_fingerprints(rows: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
    output: set[tuple[str, str, str]] = set()
    for row in rows:
        label = row_label(row)
        text = norm_text(row_text(row))
        case_id = str(row.get("case_id") or "")
        if label and text:
            output.add((case_id, text, label))
            output.add(("", text, label))
    return output


def manifest_by_case() -> dict[str, dict[str, str]]:
    rows = read_csv(MANIFEST_PATH)
    return {str(row.get("case_id") or ""): row for row in rows}


def conventional_paths(case_id: str) -> dict[str, Path]:
    return {
        "raw_transcript": ROOT / "data" / "corpus" / "raw" / "transcripts" / f"{case_id}.txt",
        "manual_transcript": ROOT / "data" / "corpus" / "manual_cases" / case_id / "raw" / "transcript.txt",
        "guidance_transcript": ROOT / "data" / "gold_guidance_calls" / "raw_calls" / f"{case_id}.txt",
        "holdout_transcript": ROOT / "data" / "gold_guidance_calls_holdout" / "raw_calls" / f"{case_id}.txt",
        "watchhold_transcript": ROOT / "data" / "gold_guidance_calls_holdout_watchlist" / "raw_calls" / f"{case_id}.txt",
        "outputs_transcript": ROOT / "outputs" / case_id / "transcript.txt",
        "evidence_objects": ROOT / "data" / "corpus" / "processed" / "evidence_objects" / f"{case_id}.evidence_objects.jsonl",
        "event_chunks": ROOT / "data" / "corpus" / "processed" / "chunks" / f"{case_id}.event_chunks.jsonl",
        "sectioned": ROOT / "data" / "corpus" / "processed" / "chunks" / f"{case_id}.transcript_sectioned.json",
    }


def first_existing(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def case_paths(case_id: str, manifest_row: dict[str, str] | None = None) -> dict[str, Path | None]:
    paths = conventional_paths(case_id)
    manifest_transcript = None
    if manifest_row:
        raw_value = manifest_row.get("transcript_local_path") or ""
        if raw_value:
            manifest_transcript = ROOT / raw_value
    raw_transcript = first_existing(
        [
            path
            for path in [
                manifest_transcript,
                paths["raw_transcript"],
                paths["guidance_transcript"],
                paths["holdout_transcript"],
                paths["watchhold_transcript"],
                paths["outputs_transcript"],
                paths["manual_transcript"],
            ]
            if path is not None
        ]
    )
    return {
        "raw_transcript": raw_transcript,
        "evidence_objects": paths["evidence_objects"] if paths["evidence_objects"].exists() else None,
        "event_chunks": paths["event_chunks"] if paths["event_chunks"].exists() else None,
        "sectioned": paths["sectioned"] if paths["sectioned"].exists() else None,
    }


def target_manual_path(case_id: str) -> str:
    return f"data/corpus/manual_cases/{case_id}/raw/transcript.txt"
