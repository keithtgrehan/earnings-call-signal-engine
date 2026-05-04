from __future__ import annotations

from pathlib import Path
from typing import Any

from data_layer.io import write_json, write_jsonl
from data_layer.schemas import NormalizedRecord, SegmentRecord
from signal_engine.adapters import asr as asr_adapter
from signal_engine.adapters import diarization as diarization_adapter


def _segment_from_record(record: NormalizedRecord) -> SegmentRecord:
    start = record.timestamps[0].start if record.timestamps else None
    end = record.timestamps[0].end if record.timestamps else None
    return SegmentRecord(
        segment_id=f"{record.id}:segment:0",
        record_id=record.id,
        start_time=start,
        end_time=end,
        speaker=str(record.metadata.get("speaker_id") or record.metadata.get("role") or "unknown"),
        text=record.text,
        domain=record.domain,
        source=record.source,
        modality=record.modality,
        audio_path=record.audio_path,
        video_path=record.video_path,
        provenance=record.provenance,
        metadata={
            "alignment_method": "transcript_first_passthrough",
            "asr_available": asr_adapter.is_available(),
            "diarization_available": diarization_adapter.is_available(),
        },
    )


def align_records(
    records: list[NormalizedRecord],
    *,
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    segments = [_segment_from_record(record) for record in records]
    status = {
        "stage": "align",
        "status": "completed",
        "dry_run": dry_run,
        "input_records": len(records),
        "segments": len(segments),
        "asr_available": asr_adapter.is_available(),
        "diarization_available": diarization_adapter.is_available(),
        "notes": [
            "Transcript-first alignment is canonical for local smoke validation.",
            "faster-whisper and pyannote readiness are reported but no model download is required.",
        ],
    }
    if not dry_run:
        write_jsonl(output_dir / "aligned_segments.jsonl", [segment.to_json_dict() for segment in segments])
        write_json(output_dir / "alignment_status.json", status)
    return {"segments": segments, "status": status}
