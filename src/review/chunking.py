from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class TranscriptChunk:
    case_id: str
    chunk_id: str
    text: str
    source_file: str
    source_artifact: str
    section: str
    speaker: str
    chunk_index: int
    start_offset: int | None
    end_offset: int | None
    provenance_hash: str
    chunk_params: dict[str, int]

    def to_record(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = {
            "case_id": self.case_id,
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "source_artifact": self.source_artifact,
            "section": self.section,
            "speaker": self.speaker,
            "chunk_index": self.chunk_index,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "provenance_hash": self.provenance_hash,
            "chunk_params": self.chunk_params,
        }
        return payload


def stable_hash(*parts: object, length: int = 16) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(str(part).encode("utf-8", errors="replace"))
        h.update(b"\x1f")
    return h.hexdigest()[:length]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def infer_case_id(path: Path) -> str:
    for parent in [path.parent, *path.parents]:
        if parent.name and parent.name not in {"raw", "processed", "labels", "chunks", "transcripts"}:
            return parent.name
    return path.stem


def _chunk_id(case_id: str, source_file: str, chunk_params: dict[str, int], index: int, start: int | None, end: int | None, text: str) -> str:
    return stable_hash(case_id, source_file, json.dumps(chunk_params, sort_keys=True), index, start, end, stable_hash(text, length=32))


def _sentence_spans(text: str) -> list[tuple[int, int]]:
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


def chunk_text(
    text: str,
    *,
    case_id: str,
    source_file: str,
    source_artifact: str = "transcript_text",
    section: str = "",
    speaker: str = "",
    chunk_size: int = 1800,
    overlap: int = 200,
    min_chunk_length: int = 200,
) -> list[TranscriptChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    normalized = normalize_text(text)
    params = {"chunk_size": chunk_size, "overlap": overlap, "min_chunk_length": min_chunk_length}
    if not normalized:
        return []

    spans = _sentence_spans(normalized)
    chunks: list[tuple[int, int]] = []
    current_start: int | None = None
    current_end = 0
    for sent_start, sent_end in spans:
        if current_start is None:
            current_start = sent_start
            current_end = sent_end
            continue
        if sent_end - current_start <= chunk_size:
            current_end = sent_end
            continue
        chunks.append((current_start, current_end))
        next_start = max(current_start, current_end - overlap)
        current_start = next_start
        current_end = sent_end
    if current_start is not None:
        chunks.append((current_start, current_end))

    records: list[TranscriptChunk] = []
    for idx, (start, end) in enumerate(chunks):
        piece = normalized[start:end].strip()
        if len(piece) < min_chunk_length and records:
            prev = records.pop()
            merged_start = prev.start_offset if prev.start_offset is not None else start
            merged = normalized[merged_start:end].strip()
            records.append(
                _make_chunk(
                    case_id,
                    source_file,
                    source_artifact,
                    section,
                    speaker,
                    len(records),
                    merged_start,
                    end,
                    merged,
                    params,
                )
            )
        elif len(piece) >= min_chunk_length or not records:
            records.append(_make_chunk(case_id, source_file, source_artifact, section, speaker, len(records), start, end, piece, params))
    return records


def _make_chunk(
    case_id: str,
    source_file: str,
    source_artifact: str,
    section: str,
    speaker: str,
    index: int,
    start: int | None,
    end: int | None,
    text: str,
    params: dict[str, int],
) -> TranscriptChunk:
    provenance_hash = stable_hash(case_id, source_file, source_artifact, section, speaker, start, end, stable_hash(text, length=32), length=24)
    return TranscriptChunk(
        case_id=case_id,
        chunk_id=_chunk_id(case_id, source_file, params, index, start, end, text),
        text=text,
        source_file=source_file,
        source_artifact=source_artifact,
        section=section,
        speaker=speaker,
        chunk_index=index,
        start_offset=start,
        end_offset=end,
        provenance_hash=provenance_hash,
        chunk_params=params,
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_text_entries(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("sections", "segments", "chunks", "items"):
            if isinstance(payload.get(key), list):
                yield from _iter_text_entries(payload[key])
                return
        if payload.get("text") or payload.get("transcript"):
            yield payload
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield from _iter_text_entries(item)


def load_transcript_file(path: Path, *, chunk_size: int = 1800, overlap: int = 200, min_chunk_length: int = 200) -> list[TranscriptChunk]:
    case_id = infer_case_id(path)
    if path.suffix == ".jsonl" and path.name.endswith(".event_chunks.jsonl"):
        return load_event_chunks(path, chunk_size=chunk_size, overlap=overlap, min_chunk_length=min_chunk_length)
    if path.suffix == ".txt":
        return chunk_text(
            path.read_text(encoding="utf-8"),
            case_id=case_id,
            source_file=str(path),
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_length=min_chunk_length,
        )
    if path.suffix == ".json":
        payload = _read_json(path)
        chunks: list[TranscriptChunk] = []
        for entry in _iter_text_entries(payload):
            text = str(entry.get("text") or entry.get("transcript") or "")
            section = str(entry.get("section") or entry.get("name") or "")
            speaker = str(entry.get("speaker") or entry.get("speaker_role") or "")
            chunks.extend(
                chunk_text(
                    text,
                    case_id=case_id,
                    source_file=str(path),
                    source_artifact=path.name,
                    section=section,
                    speaker=speaker,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    min_chunk_length=min_chunk_length,
                )
            )
        return [_replace_index(chunk, idx) for idx, chunk in enumerate(chunks)]
    return []


def _replace_index(chunk: TranscriptChunk, index: int) -> TranscriptChunk:
    if chunk.chunk_index == index:
        return chunk
    return _make_chunk(
        chunk.case_id,
        chunk.source_file,
        chunk.source_artifact,
        chunk.section,
        chunk.speaker,
        index,
        chunk.start_offset,
        chunk.end_offset,
        chunk.text,
        chunk.chunk_params,
    )


def load_event_chunks(path: Path, *, chunk_size: int = 1800, overlap: int = 200, min_chunk_length: int = 1) -> list[TranscriptChunk]:
    params = {"chunk_size": chunk_size, "overlap": overlap, "min_chunk_length": min_chunk_length}
    records: list[TranscriptChunk] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            text = normalize_text(str(row.get("text") or ""))
            if len(text) < min_chunk_length:
                continue
            case_id = str(row.get("case_id") or infer_case_id(path))
            start = row.get("start")
            end = row.get("end")
            start_i = int(start) if isinstance(start, int) else None
            end_i = int(end) if isinstance(end, int) else None
            records.append(
                _make_chunk(
                    case_id,
                    str(path),
                    str(row.get("source_artifact") or path.name),
                    str(row.get("section") or ""),
                    str(row.get("speaker") or row.get("speaker_role") or ""),
                    idx,
                    start_i,
                    end_i,
                    text,
                    params,
                )
            )
    return records


def find_transcript_inputs(root: Path) -> list[Path]:
    event_chunks = sorted(root.glob("**/*.event_chunks.jsonl"))
    if event_chunks:
        return event_chunks
    names = {"transcript.txt", "transcript.json", "transcript_sectioned.json"}
    return sorted(path for path in root.glob("**/*") if path.is_file() and path.name in names)


def load_transcript_chunks(
    root: Path,
    *,
    chunk_size: int = 1800,
    overlap: int = 200,
    min_chunk_length: int = 200,
) -> list[TranscriptChunk]:
    chunks: list[TranscriptChunk] = []
    for path in find_transcript_inputs(root):
        chunks.extend(load_transcript_file(path, chunk_size=chunk_size, overlap=overlap, min_chunk_length=min_chunk_length))
    seen: set[str] = set()
    unique: list[TranscriptChunk] = []
    for chunk in chunks:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        unique.append(chunk)
    return unique


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
