from __future__ import annotations

import glob
import json
import re
from pathlib import Path
from typing import Any

from .schema import blank_human_fields, normalize_label

TEXT_SUFFIXES = {".md", ".markdown"}
JSONL_SUFFIXES = {".jsonl"}


def resolve_input_files(values: list[str], *, include_markdown: bool = True, include_jsonl: bool = True) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    suffixes: set[str] = set()
    if include_markdown:
        suffixes.update(TEXT_SUFFIXES)
    if include_jsonl:
        suffixes.update(JSONL_SUFFIXES)
    for value in values:
        matches = [Path(item) for item in glob.glob(value)] or [Path(value)]
        for match in matches:
            if match.is_dir():
                candidates = [path for path in sorted(match.rglob("*")) if path.is_file() and path.suffix.lower() in suffixes]
            else:
                candidates = [match] if match.exists() and match.suffix.lower() in suffixes else []
            for candidate in candidates:
                resolved = candidate.resolve()
                if resolved not in seen:
                    files.append(candidate)
                    seen.add(resolved)
    return files


def parse_files(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix in TEXT_SUFFIXES:
            rows.extend(parse_markdown_packet(path))
        elif suffix in JSONL_SUFFIXES:
            rows.extend(parse_weak_label_jsonl(path))
    return dedupe_candidate_ids(rows)


def infer_case_id(*values: str) -> str:
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        match = re.search(r"\b([A-Z]{2,6}_\d{4}_Q[1-4](?:_[A-Za-z0-9]+)?)\b", text)
        if match:
            return match.group(1)
        match = re.search(r"\b([A-Za-z0-9]+_[A-Za-z0-9]+_[A-Za-z0-9]+)\b", text)
        if match:
            return match.group(1)
    return ""


def clean_value(value: str) -> str:
    text = value.strip()
    if text.startswith("`") and text.endswith("`"):
        text = text[1:-1]
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text.strip()


def parse_bullets(block: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"\s*[-*]\s*([A-Za-z0-9_ -]+)\s*:\s*(.*)\s*$", line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            metadata[key] = clean_value(match.group(2))
    return metadata


def fenced_evidence(block: str) -> str:
    match = re.search(r"```(?:text)?\s*\n(.*?)\n```", block, flags=re.S | re.I)
    return match.group(1).strip() if match else ""


def blockquote_evidence(block: str) -> str:
    lines: list[str] = []
    in_quote = False
    for line in block.splitlines():
        if line.lstrip().startswith(">"):
            in_quote = True
            lines.append(line.lstrip()[1:].strip())
        elif in_quote and line.strip():
            lines.append(line.strip())
        elif in_quote:
            break
    return "\n".join(lines).strip()


def split_combined_packet(text: str, fallback_source: str) -> list[tuple[str, str, str]]:
    case_matches = list(re.finditer(r"(?im)^CASE:\s*(.+?)\s*$", text))
    if not case_matches:
        source = ""
        source_match = re.search(r"(?im)^SOURCE:\s*(.+?)\s*$", text)
        if source_match:
            source = source_match.group(1).strip()
        return [("", source or fallback_source, text)]
    sections: list[tuple[str, str, str]] = []
    for index, match in enumerate(case_matches):
        start = match.start()
        end = case_matches[index + 1].start() if index + 1 < len(case_matches) else len(text)
        section = text[start:end]
        source_match = re.search(r"(?im)^SOURCE:\s*(.+?)\s*$", section)
        sections.append((match.group(1).strip(), source_match.group(1).strip() if source_match else fallback_source, section))
    return sections


def section_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^(#{2,4})\s+(.+?)\s*$", text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        title = match.group(2).strip()
        if not candidate_title(title):
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((title, text[start:end]))
    return blocks


def candidate_title(title: str) -> bool:
    lowered = title.lower()
    return bool(re.search(r"\bcand(?:idate)?[-_ ]?\d+\b", lowered) or "_weak_" in lowered or lowered.startswith("priority_review_"))


def parse_markdown_packet(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, str]] = []
    header_match = re.search(r"(?im)^#\s*Human Labeling Packet:\s*(.+?)\s*$", text)
    header_case = header_match.group(1).strip() if header_match else ""
    for section_case, section_source, section in split_combined_packet(text, str(path)):
        case_id = section_case or header_case or infer_case_id(str(path))
        for title, block in section_blocks(section):
            metadata = parse_bullets(block)
            explicit_id = metadata.get("candidate_id") or metadata.get("id")
            inferred_id = title.replace("-", "_").replace(" ", "_")
            if re.fullmatch(r"(?i)cand[_ -]?\d+", title.strip()) and case_id:
                inferred_id = f"{case_id}_{inferred_id.upper()}"
            candidate_id = explicit_id or inferred_id
            evidence = fenced_evidence(block) or blockquote_evidence(block)
            suggested_label = metadata.get("suggested_label") or metadata.get("predicted_label") or metadata.get("weak_label") or metadata.get("label") or ""
            confidence = metadata.get("suggested_confidence") or metadata.get("confidence") or metadata.get("deterministic_confidence") or ""
            reason = metadata.get("reason") or metadata.get("evidence_terms") or metadata.get("trigger_terms") or metadata.get("warning") or ""
            source_file = metadata.get("source_file") or metadata.get("source_path") or section_source or str(path)
            row_case_id = case_id or infer_case_id(candidate_id, source_file, str(path))
            warning_parts: list[str] = []
            if not row_case_id:
                warning_parts.append("missing_case_id")
            if not evidence:
                warning_parts.append("missing_evidence_span")
            if not suggested_label:
                warning_parts.append("missing_suggested_label")
            if not confidence:
                warning_parts.append("missing_suggested_confidence")
            if not reason:
                warning_parts.append("missing_reason")
            rows.append(
                base_row(
                    case_id=row_case_id,
                    candidate_id=candidate_id,
                    suggested_label=suggested_label,
                    suggested_confidence=confidence,
                    reason=reason,
                    source_file=source_file,
                    evidence_span=evidence,
                    packet_file=str(path),
                    source_type="human_labeling_packet",
                    parser_warning=";".join(warning_parts),
                )
            )
    if not rows and text.strip():
        rows.append(
            base_row(
                case_id=header_case or infer_case_id(str(path)),
                candidate_id=f"{Path(path).stem}_unparsed",
                suggested_label="",
                suggested_confidence="",
                reason="",
                source_file=str(path),
                evidence_span="",
                packet_file=str(path),
                source_type="human_labeling_packet",
                parser_warning="no_candidate_blocks_found",
            )
        )
    return rows


def parse_weak_label_jsonl(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        warning_parts: list[str] = []
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            payload = {}
            warning_parts.append(f"invalid_json_line_{index}")
        if not isinstance(payload, dict):
            payload = {}
            warning_parts.append(f"non_object_json_line_{index}")
        candidate_id = str(payload.get("candidate_id") or payload.get("id") or f"{path.stem}_row_{index:04d}").strip()
        evidence = first_text(payload, "evidence_span", "text", "text_span", "evidence_text", "matched_text", "segment_text")
        label = first_text(payload, "suggested_label", "predicted_label", "weak_label", "label", "type", "signal_type")
        confidence = first_text(payload, "suggested_confidence", "confidence", "score")
        reason = reason_from_payload(payload)
        source_file = first_text(payload, "source_file", "source_path", "source") or str(path)
        case_id = first_text(payload, "case_id", "call_id", "source_case_id") or infer_case_id(candidate_id, source_file, str(path))
        if not evidence:
            warning_parts.append("missing_evidence_span")
        if not label:
            warning_parts.append("missing_suggested_label")
        if not confidence:
            warning_parts.append("missing_suggested_confidence")
        if not reason:
            warning_parts.append("missing_reason")
        rows.append(
            base_row(
                case_id=case_id,
                candidate_id=candidate_id,
                suggested_label=label,
                suggested_confidence=confidence,
                reason=reason,
                source_file=source_file,
                evidence_span=evidence,
                packet_file=str(path),
                source_type="weak_label_jsonl",
                parser_warning=";".join(warning_parts),
            )
        )
    return rows


def first_text(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        text = str(value or "").strip()
        if text:
            return text
    return ""


def reason_from_payload(payload: dict[str, Any]) -> str:
    for key in ("reason", "label_reason", "rationale", "warning", "evidence_terms", "trigger_terms"):
        value = payload.get(key)
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        text = str(value or "").strip()
        if text:
            return text
    return ""


def base_row(
    *,
    case_id: str,
    candidate_id: str,
    suggested_label: str,
    suggested_confidence: str,
    reason: str,
    source_file: str,
    evidence_span: str,
    packet_file: str,
    source_type: str,
    parser_warning: str,
) -> dict[str, str]:
    normalized = normalize_label(suggested_label)
    return {
        "case_id": case_id,
        "candidate_id": candidate_id,
        "suggested_label": suggested_label,
        "suggested_confidence": suggested_confidence,
        "reason": reason,
        "source_file": source_file,
        "evidence_span": evidence_span,
        "context_before": "",
        "context_after": "",
        "surrounding_context": "",
        "packet_file": packet_file,
        "transcript_file_if_matched": "",
        "evidence_match_status": "not_checked",
        "parser_warning": parser_warning,
        **blank_human_fields(),
        "normalized_label": normalized,
        "source_type": source_type,
        "rule_family": "",
        "likely_review_priority": "",
        "priority_reason": "",
        "is_likely_boilerplate": "",
        "needs_context_lookup": "yes",
        "duplicate_key": "",
        "duplicate_count": "1",
    }


def dedupe_candidate_ids(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    for row in rows:
        candidate_id = row.get("candidate_id", "")
        if candidate_id:
            counts[candidate_id] = counts.get(candidate_id, 0) + 1
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        candidate_id = row.get("candidate_id", "")
        row["duplicate_key"] = candidate_id
        row["duplicate_count"] = str(counts.get(candidate_id, 1))
        if candidate_id and candidate_id in seen:
            continue
        if candidate_id:
            seen.add(candidate_id)
        deduped.append(row)
    return deduped
