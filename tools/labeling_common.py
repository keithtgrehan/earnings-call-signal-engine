from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from typing import Any

SIGNAL_LABELS = {"risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral"}
CONFIDENCE_MAP = {"high": 0.9, "medium": 0.6, "low": 0.35, "": 0.0}
BOILERPLATE_TERMS = ("operator", "copyright", "safe harbor", "forward-looking", "presentation", "webcast replay")
DISCLAIMER_TERMS = ("forward-looking statements", "risk factors", "actual results", "sec filings", "not undertake")
ADMIN_TERMS = ("thank you for standing by", "conference call", "question-and-answer session", "press *", "operator instructions")
HIGH_BUSINESS_TERMS = (
    "guidance",
    "revenue",
    "margin",
    "renewal",
    "pricing",
    "budget",
    "escalate",
    "refund",
    "churn",
    "risk",
    "commit",
    "pilot",
    "procurement",
    "unresolved",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def read_csv_text(text: str) -> list[dict[str, Any]]:
    handle = io.StringIO(text)
    reader = csv.DictReader(handle)
    return [dict(row) for row in reader]


def stable_id(*parts: str) -> str:
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"cand_{digest}"


def normalize_confidence(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().lower()
    if text in CONFIDENCE_MAP:
        return CONFIDENCE_MAP[text]
    try:
        number = float(text)
    except ValueError:
        return 0.0
    if number > 1.0:
        number /= 100.0
    return round(max(0.0, min(1.0, number)), 4)


def normalize_label(value: Any) -> str:
    label = str(value or "").strip()
    if label in SIGNAL_LABELS:
        return label
    lowered = label.lower().replace("-", "_").replace(" ", "_")
    return lowered if lowered in SIGNAL_LABELS else label


def infer_case_id(row: dict[str, Any], source_name: str) -> str:
    for key in ("case_id", "call_id", "source_call_id", "conversation_id", "source_file", "source_path"):
        value = str(row.get(key) or "").strip()
        if value:
            return Path(value).stem
    return Path(source_name).stem


def row_text(row: dict[str, Any]) -> str:
    for key in ("text", "evidence_text", "matched_text", "segment_text", "utterance", "content"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def row_label(row: dict[str, Any]) -> str:
    for key in ("weak_label", "suggested_label", "current_label", "signal_family", "label", "guidance_change_label"):
        value = normalize_label(row.get(key))
        if value:
            return value
    return ""


def row_reason(row: dict[str, Any]) -> str:
    for key in ("reason", "label_reason", "rationale", "notes", "suggested_evidence_terms", "evidence_terms"):
        value = row.get(key)
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        text = str(value or "").strip()
        if text:
            return text
    return ""


def row_confidence(row: dict[str, Any]) -> float:
    for key in ("confidence", "suggestion_confidence", "label_confidence", "reviewer_confidence"):
        if str(row.get(key) or "").strip():
            return normalize_confidence(row.get(key))
    return 0.0


def noise_flag(text: str) -> str:
    lowered = " ".join(text.lower().split())
    flags: list[str] = []
    if any(term in lowered for term in BOILERPLATE_TERMS):
        flags.append("boilerplate")
    if any(term in lowered for term in DISCLAIMER_TERMS):
        flags.append("disclaimer")
    if any(term in lowered for term in ADMIN_TERMS):
        flags.append("admin_text")
    return ";".join(flags)


def is_high_business_context(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in HIGH_BUSINESS_TERMS)


def candidate_from_row(row: dict[str, Any], *, source_name: str, row_index: int) -> dict[str, Any] | None:
    text = row_text(row)
    if not text:
        return None
    weak_label = row_label(row)
    candidate_id = str(row.get("candidate_id") or row.get("id") or "").strip()
    if not candidate_id:
        candidate_id = stable_id(source_name, str(row_index), text, weak_label)
    return {
        "candidate_id": candidate_id,
        "source": source_name,
        "source_row": row_index,
        "case_id": infer_case_id(row, source_name),
        "weak_label": weak_label,
        "confidence": row_confidence(row),
        "reason": row_reason(row),
        "text": text,
        "noise_flag": noise_flag(text),
        "duplicate_of": "",
    }


def parse_markdown_candidates(text: str, *, source_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    table_lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) >= 2:
        header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
        for line in table_lines[2:]:
            values = [cell.strip() for cell in line.strip("|").split("|")]
            if len(values) == len(header):
                rows.append(dict(zip(header, values, strict=True)))
    if rows:
        return rows
    block_pattern = re.compile(r"(?:candidate[_ -]?id|id)\s*[:` ]+([A-Za-z0-9_.:-]+).*?(?:text)\s*[:` ]+(.+?)(?=\n\s*\n|\Z)", re.I | re.S)
    for match in block_pattern.finditer(text):
        rows.append({"id": match.group(1).strip(), "text": " ".join(match.group(2).split())})
    if not rows and text.strip():
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if len(paragraph.split()) >= 8]
        for index, paragraph in enumerate(paragraphs):
            rows.append({"id": f"{Path(source_name).stem}_paragraph_{index:04d}", "text": " ".join(paragraph.split())})
    return rows


def parse_payload(name: str, text: str) -> list[dict[str, Any]]:
    suffix = Path(name).suffix.lower()
    if suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if suffix == ".json":
        payload = json.loads(text)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("candidates", "rows", "items", "examples"):
                if isinstance(payload.get(key), list):
                    return [item for item in payload[key] if isinstance(item, dict)]
            return [payload]
    if suffix == ".csv":
        return read_csv_text(text)
    if suffix in {".md", ".markdown", ".txt"}:
        return parse_markdown_candidates(text, source_name=name)
    return []


def iter_packet_files(packet: Path) -> list[tuple[str, str]]:
    if packet.is_dir():
        files = [
            path
            for path in sorted(packet.rglob("*"))
            if path.is_file() and path.suffix.lower() in {".jsonl", ".json", ".csv", ".md", ".markdown", ".txt"}
        ]
        return [(str(path), path.read_text(encoding="utf-8", errors="replace")) for path in files]
    if packet.suffix.lower() == ".zip":
        items: list[tuple[str, str]] = []
        with zipfile.ZipFile(packet) as archive:
            for info in sorted(archive.infolist(), key=lambda item: item.filename):
                path = Path(info.filename)
                if info.is_dir() or path.is_absolute() or ".." in path.parts:
                    continue
                if path.suffix.lower() not in {".jsonl", ".json", ".csv", ".md", ".markdown", ".txt"}:
                    continue
                with archive.open(info) as handle:
                    items.append((info.filename, handle.read().decode("utf-8", errors="replace")))
        return items
    return [(str(packet), packet.read_text(encoding="utf-8", errors="replace"))]


def parse_packet(packet: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_text: dict[tuple[str, str, str], str] = {}
    for source_name, text in iter_packet_files(packet):
        for index, row in enumerate(parse_payload(source_name, text)):
            if not isinstance(row, dict):
                continue
            candidate = candidate_from_row(row, source_name=source_name, row_index=index)
            if candidate is None:
                continue
            key = (candidate["case_id"], candidate["weak_label"], " ".join(candidate["text"].lower().split()))
            if key in seen_text:
                candidate["duplicate_of"] = seen_text[key]
            else:
                seen_text[key] = candidate["candidate_id"]
            candidates.append(candidate)
    return candidates


def load_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise ValueError(f"Unsupported candidate file: {path}")


def review_decision(row: dict[str, Any]) -> str:
    for key in ("review_decision", "accepted"):
        decision = str(row.get(key) or "").strip().lower()
        if decision in {"accept", "accepted", "yes", "true", "1"}:
            return "accepted"
        if decision in {"reject", "rejected", "no", "false", "0"}:
            return "rejected"
        if decision in {"unclear", "unsure", "maybe"}:
            return "unclear"
    return ""

