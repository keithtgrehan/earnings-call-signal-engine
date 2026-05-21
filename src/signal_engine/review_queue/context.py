from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import glob
from pathlib import Path
import re

TRANSCRIPT_SUFFIXES = {".txt"}


@dataclass(frozen=True)
class TranscriptRecord:
    path: Path
    text: str
    keys: set[str]


@dataclass(frozen=True)
class MatchResult:
    transcript_file_if_matched: str = ""
    evidence_match_status: str = "no_transcripts_available"
    context_before: str = ""
    context_after: str = ""
    surrounding_context: str = ""


def resolve_transcript_files(values: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for value in values:
        matches = [Path(item) for item in glob.glob(value)] or [Path(value)]
        for match in matches:
            if match.is_dir():
                candidates = [path for path in sorted(match.rglob("*.txt")) if path.is_file() and is_transcript_like(path)]
            else:
                candidates = [match] if match.exists() and match.suffix.lower() in TRANSCRIPT_SUFFIXES else []
            for candidate in candidates:
                resolved = candidate.resolve()
                if resolved not in seen:
                    files.append(candidate)
                    seen.add(resolved)
    return files


def is_transcript_like(path: Path) -> bool:
    name = path.name.lower()
    if "transcript" in name:
        return True
    return path.parent.name.lower() in {"raw", "transcript", "transcripts"}


class TranscriptIndex:
    def __init__(self, paths: list[Path]):
        self.records = [TranscriptRecord(path=path, text=path.read_text(encoding="utf-8", errors="replace"), keys=case_keys(path)) for path in paths]

    def candidates_for_case(self, case_id: str) -> list[TranscriptRecord]:
        if not self.records:
            return []
        normalized = case_id.strip()
        matched = [record for record in self.records if normalized and normalized in record.keys]
        if matched:
            return matched
        prefix = normalized.split("_call")[0].split("_holdout")[0].split("_watch")[0]
        if prefix:
            matched = [record for record in self.records if prefix in record.keys]
            if matched:
                return matched
        return self.records

    def match(self, case_id: str, evidence: str, *, context_chars: int, context_sentences: int) -> MatchResult:
        evidence = str(evidence or "").strip()
        if not self.records:
            return MatchResult()
        if not evidence:
            return MatchResult(evidence_match_status="missing_evidence_span")
        for record in self.candidates_for_case(case_id):
            exact = record.text.find(evidence)
            if exact >= 0:
                return build_match(record, exact, exact + len(evidence), "exact_match", context_chars, context_sentences)
            normalized = normalized_whitespace_match(record.text, evidence)
            if normalized is not None:
                start, end = normalized
                return build_match(record, start, end, "normalized_whitespace_match", context_chars, context_sentences)
            fuzzy = fuzzy_match(record.text, evidence)
            if fuzzy is not None:
                start, end = fuzzy
                return build_match(record, start, end, "fuzzy_match", context_chars, context_sentences)
        return MatchResult(evidence_match_status="unmatched_context")


def case_keys(path: Path) -> set[str]:
    keys = {path.stem}
    parts = list(path.parts)
    for index, part in enumerate(parts):
        if part in {"high_signal_cases", "manual_sources", "manual_cases"} and index + 1 < len(parts):
            keys.add(parts[index + 1])
    for part in parts:
        if re.fullmatch(r"[A-Z]{2,6}_\d{4}_Q[1-4](?:_[A-Za-z0-9]+)?", part):
            keys.add(part)
    if path.name == "transcript.txt" and len(parts) >= 3:
        keys.add(parts[-3])
    if path.name == "transcript_clean.txt" and len(parts) >= 3:
        keys.add(parts[-3])
    return {key for key in keys if key}


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    mapping: list[int] = []
    pending_space = False
    for index, char in enumerate(text):
        if char.isspace():
            pending_space = bool(chars)
            continue
        if pending_space:
            chars.append(" ")
            mapping.append(index)
            pending_space = False
        chars.append(char.lower())
        mapping.append(index)
    return "".join(chars), mapping


def normalized_whitespace_match(transcript: str, evidence: str) -> tuple[int, int] | None:
    normalized_transcript, mapping = normalize_with_map(transcript)
    normalized_evidence, _ = normalize_with_map(evidence)
    if not normalized_evidence:
        return None
    start = normalized_transcript.find(normalized_evidence)
    if start < 0:
        return None
    end = start + len(normalized_evidence) - 1
    return mapping[start], min(len(transcript), mapping[end] + 1)


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in re.finditer(r"(?<=[.!?])\s+", text):
        end = match.end()
        if end > start:
            spans.append((start, end))
        start = end
    if start < len(text):
        spans.append((start, len(text)))
    return spans or [(0, len(text))]


def fuzzy_match(transcript: str, evidence: str) -> tuple[int, int] | None:
    evidence_norm = " ".join(evidence.lower().split())
    evidence_tokens = set(re.findall(r"[a-z0-9$%]+", evidence_norm))
    if len(evidence_tokens) < 4:
        return None
    spans = sentence_spans(transcript)
    best: tuple[float, int, int] | None = None
    for index in range(len(spans)):
        for window in range(1, min(5, len(spans) - index + 1)):
            start = spans[index][0]
            end = spans[index + window - 1][1]
            chunk_norm = " ".join(transcript[start:end].lower().split())
            chunk_tokens = set(re.findall(r"[a-z0-9$%]+", chunk_norm))
            if not chunk_tokens:
                continue
            overlap = len(evidence_tokens & chunk_tokens) / max(1, len(evidence_tokens))
            ratio = SequenceMatcher(None, evidence_norm[:1200], chunk_norm[:1200]).ratio()
            score = max(overlap, ratio)
            if best is None or score > best[0]:
                best = (score, start, end)
    if best and best[0] >= 0.72:
        return best[1], best[2]
    return None


def build_match(record: TranscriptRecord, start: int, end: int, status: str, context_chars: int, context_sentences: int) -> MatchResult:
    before_start, after_end = context_bounds(record.text, start, end, context_chars, context_sentences)
    return MatchResult(
        transcript_file_if_matched=str(record.path),
        evidence_match_status=status,
        context_before=record.text[before_start:start].strip(),
        context_after=record.text[end:after_end].strip(),
        surrounding_context=record.text[before_start:after_end].strip(),
    )


def context_bounds(text: str, start: int, end: int, context_chars: int, context_sentences: int) -> tuple[int, int]:
    spans = sentence_spans(text)
    sentence_index = next((index for index, span in enumerate(spans) if span[0] <= start < span[1]), 0)
    before_index = max(0, sentence_index - max(0, context_sentences))
    after_index = min(len(spans) - 1, sentence_index + max(0, context_sentences))
    before_start = max(spans[before_index][0], start - max(0, context_chars))
    after_end = min(spans[after_index][1], end + max(0, context_chars))
    return before_start, after_end
