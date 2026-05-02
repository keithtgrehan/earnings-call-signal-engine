from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from signal_engine.signal_baseline import collect_local_signal_examples

from .io import read_jsonl, sha256_file, write_json, write_jsonl
from .schemas import DatasetIngestionStatus, Modality, NormalizedRecord, Provenance, normalize_domain


@dataclass(frozen=True)
class DatasetConnector:
    dataset_id: str
    modality: str
    access: str
    local_candidates: tuple[str, ...] = ()
    reason_when_missing: str = "Dataset is not available locally; connector records status without downloading."


DATASET_CONNECTORS: tuple[DatasetConnector, ...] = (
    DatasetConnector("GoEmotions", "text", "public_hf", ("data/external/goemotions.jsonl",)),
    DatasetConnector("EmotionLines", "text", "public", ("data/external/emotionlines.jsonl",)),
    DatasetConnector("MELD", "multimodal", "public_large", ("data/external/meld.jsonl",)),
    DatasetConnector("IEMOCAP", "multimodal", "license_required", ("data/external/iemocap.jsonl",)),
    DatasetConnector("RAVDESS", "audio", "public_large", ("data/external/ravdess.jsonl",)),
    DatasetConnector("CREMA-D", "audio", "public_large", ("data/external/crema_d.jsonl",)),
    DatasetConnector("Financial PhraseBank", "text", "local_or_manual", ("data/external/financial_phrasebank.jsonl",)),
    DatasetConnector("earnings_call_transcripts", "text", "existing_corpus", ()),
    DatasetConnector("MultiWOZ", "text", "public_hf", ("data/external/multiwoz.jsonl",)),
    DatasetConnector("DailyDialog", "text", "public_hf", ("data/external/dailydialog.jsonl",)),
    DatasetConnector("Customer Support on Twitter", "text", "public_large", ("data/external/customer_support_twitter.jsonl",)),
    DatasetConnector("AffectNet", "video", "license_required", ("data/external/affectnet.jsonl",)),
    DatasetConnector("FER2013", "video", "public", ("data/external/fer2013.jsonl",)),
    DatasetConnector("LibriSpeech", "audio", "public_large", ("data/external/librispeech.jsonl",)),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _record_from_row(row: dict[str, Any], *, dataset_id: str, row_index: int) -> NormalizedRecord:
    text = str(row.get("text") or row.get("utterance") or row.get("sentence") or "").strip()
    return NormalizedRecord(
        id=str(row.get("id") or row.get("case_id") or f"{dataset_id}:{row_index}"),
        text=text,
        emotion=str(row.get("emotion") or row.get("gold_label") or "").strip() or None,
        sentiment=str(row.get("sentiment") or "").strip() or None,
        domain=normalize_domain(str(row.get("domain") or "general")),
        source=dataset_id,
        modality=Modality(str(row.get("modality") or "text")),
        audio_path=str(row.get("audio_path") or "").strip() or None,
        video_path=str(row.get("video_path") or "").strip() or None,
        provenance=Provenance(str(row.get("provenance") or row.get("label_source") or "weak")),
        metadata={key: value for key, value in row.items() if key not in {"text", "emotion", "sentiment"}},
    )


def _load_local_jsonl(path: Path, *, dataset_id: str) -> tuple[list[NormalizedRecord], list[dict[str, Any]]]:
    records: list[NormalizedRecord] = []
    rejected: list[dict[str, Any]] = []
    for index, row in enumerate(read_jsonl(path)):
        try:
            record = _record_from_row(row, dataset_id=dataset_id, row_index=index)
            if not record.text and not record.audio_path and not record.video_path:
                raise ValueError("record has no text, audio_path, or video_path")
            records.append(record)
        except Exception as exc:  # noqa: BLE001 - rejection artifact should retain all failures.
            rejected.append({"dataset_id": dataset_id, "row_index": index, "reason": str(exc), "row": row})
    return records, rejected


def _load_existing_fixtures(root: Path) -> tuple[list[NormalizedRecord], list[dict[str, Any]]]:
    records: list[NormalizedRecord] = []
    rejected: list[dict[str, Any]] = []
    for index, row in enumerate(collect_local_signal_examples(root=root)):
        try:
            records.append(
                NormalizedRecord(
                    id=f"local_signal_fixture:{index}",
                    text=str(row["text"]),
                    emotion=None,
                    sentiment=None,
                    domain=normalize_domain(str(row.get("domain"))),
                    source=str(row.get("source_path") or "local_signal_fixture"),
                    modality=Modality.text,
                    provenance=Provenance.synthetic,
                    metadata=row,
                )
            )
        except Exception as exc:  # noqa: BLE001
            rejected.append({"dataset_id": "local_signal_fixture", "row_index": index, "reason": str(exc), "row": row})

    emotion_fixture = root / "data" / "signal_engine_2_0" / "emotion_benchmark" / "sample_emotion_cases.jsonl"
    if emotion_fixture.exists():
        extra, extra_rejected = _load_local_jsonl(emotion_fixture, dataset_id="signal_engine_2_0_emotion_fixture")
        records.extend(extra)
        rejected.extend(extra_rejected)
    return records, rejected


def _connector_status(root: Path, connector: DatasetConnector) -> tuple[DatasetIngestionStatus, list[NormalizedRecord], list[dict[str, Any]]]:
    if connector.dataset_id == "earnings_call_transcripts":
        records, rejected = _load_existing_fixtures(root)
        return (
            DatasetIngestionStatus(
                dataset_id=connector.dataset_id,
                status="completed",
                access=connector.access,
                modality=connector.modality,
                loaded_rows=len(records),
                rejected_rows=len(rejected),
                reason="Loaded repo-native fixtures and existing transcript-derived samples for deterministic smoke validation.",
            ),
            records,
            rejected,
        )

    for relative in connector.local_candidates:
        path = root / relative
        if path.exists():
            records, rejected = _load_local_jsonl(path, dataset_id=connector.dataset_id)
            return (
                DatasetIngestionStatus(
                    dataset_id=connector.dataset_id,
                    status="completed",
                    source_path=str(path),
                    access=connector.access,
                    modality=connector.modality,
                    loaded_rows=len(records),
                    rejected_rows=len(rejected),
                    checksum_sha256=sha256_file(path),
                ),
                records,
                rejected,
            )

    return (
        DatasetIngestionStatus(
            dataset_id=connector.dataset_id,
            status="skipped",
            access=connector.access,
            modality=connector.modality,
            reason=connector.reason_when_missing,
        ),
        [],
        [],
    )


def ingest_datasets(*, root: Path | None = None, output_dir: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    repo_root = root or _repo_root()
    out_dir = output_dir or repo_root / "data" / "processed" / "multimodal_engine"
    statuses: list[DatasetIngestionStatus] = []
    records: list[NormalizedRecord] = []
    rejected_rows: list[dict[str, Any]] = []

    for connector in DATASET_CONNECTORS:
        status, connector_records, connector_rejected = _connector_status(repo_root, connector)
        statuses.append(status)
        records.extend(connector_records)
        rejected_rows.extend(connector_rejected)

    manifest = {
        "schema_version": "dataset_ingestion_manifest.v1",
        "dry_run": dry_run,
        "dataset_statuses": [status.to_json_dict() for status in statuses],
        "loaded_rows": len(records),
        "rejected_rows": len(rejected_rows),
        "output_records_path": str(out_dir / "normalized_records.jsonl"),
        "rejected_records_path": str(out_dir / "rejected_records.jsonl"),
    }

    if not dry_run:
        write_jsonl(out_dir / "normalized_records.jsonl", [record.to_json_dict() for record in records])
        write_jsonl(out_dir / "rejected_records.jsonl", rejected_rows)
        write_json(out_dir / "ingestion_manifest.json", manifest)
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "dry_run_ingestion_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return {"records": records, "rejected_rows": rejected_rows, "manifest": manifest}
