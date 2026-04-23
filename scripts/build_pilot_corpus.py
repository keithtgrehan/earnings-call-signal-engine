from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
from typing import Any
from urllib.parse import urlparse

from earnings_call_sentiment.corpus import (
    CorpusCase,
    build_manifest_validation_summary,
    ensure_corpus_layout,
    repo_root,
    to_repo_relative,
    write_manifest_csv,
    write_manifest_jsonl,
)
from earnings_call_sentiment.corpus_artifacts import export_case_artifacts, load_evidence_rows
from earnings_call_sentiment.retrieval_index import RetrievalRecord, write_retrieval_index

LEGACY_MANIFEST_DIRS = [
    Path("data/gold_guidance_calls"),
    Path("data/gold_guidance_calls_holdout"),
    Path("data/gold_guidance_calls_holdout_watchlist"),
    Path("data/nvda_2025_historical_calls"),
    Path("data/watchlist_earnings_candidates"),
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_token(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _match_raw_transcript(
    *,
    manifest_dir: Path,
    row: dict[str, str],
) -> Path | None:
    raw_dir = manifest_dir / "raw_calls"
    if not raw_dir.exists():
        return None
    candidates = sorted(raw_dir.glob("*.txt"))
    call_id = str(row.get("call_id", "")).strip().lower()
    ticker = _normalize_token(str(row.get("ticker", "")))
    quarter = _normalize_token(str(row.get("quarter", "")))
    event_date = str(row.get("event_date", "")).strip()

    for path in candidates:
        stem_lower = path.stem.lower()
        if call_id and call_id in stem_lower:
            return path

    for path in candidates:
        stem = _normalize_token(path.stem)
        if ticker and ticker in stem and quarter and quarter in stem:
            return path

    for path in candidates:
        stem = path.stem
        if ticker and ticker.lower() in stem.lower() and event_date and event_date in stem:
            return path
    return None


def _load_candidates() -> list[dict[str, Any]]:
    repo = repo_root()
    candidates: list[dict[str, Any]] = []
    for relative_dir in LEGACY_MANIFEST_DIRS:
        manifest_dir = repo / relative_dir
        call_manifest_path = manifest_dir / "call_manifest.csv"
        official_manifest_path = manifest_dir / "official_source_manifest.csv"
        if not call_manifest_path.exists():
            continue
        official_rows = {
            str(row.get("call_id", "")): row
            for row in (_read_csv(official_manifest_path) if official_manifest_path.exists() else [])
        }
        for row in _read_csv(call_manifest_path):
            raw_transcript_path = _match_raw_transcript(manifest_dir=manifest_dir, row=row)
            official_row = official_rows.get(str(row.get("call_id", "")), {})
            case_id = raw_transcript_path.stem if raw_transcript_path else ""
            processed_dir = repo / "outputs" / case_id if case_id else None
            processed_case_dir = (
                processed_dir if processed_dir and processed_dir.exists() and (processed_dir / "transcript.json").exists() else None
            )
            candidates.append(
                {
                    "manifest_dir": str(relative_dir),
                    "call_manifest_path": str(call_manifest_path.relative_to(repo)),
                    "official_manifest_path": str(official_manifest_path.relative_to(repo))
                    if official_manifest_path.exists()
                    else "",
                    "row": row,
                    "official_row": official_row,
                    "raw_transcript_path": raw_transcript_path,
                    "case_id": case_id,
                    "processed_case_dir": processed_case_dir,
                }
            )
    return candidates


def _sort_key(candidate: dict[str, Any]) -> tuple[int, int, int, str]:
    row = candidate["row"]
    official_row = candidate["official_row"]
    return (
        1 if candidate["raw_transcript_path"] else 0,
        1 if candidate["processed_case_dir"] else 0,
        1 if str(official_row.get("metadata_status", "")) == "confirmed" else 0,
        str(row.get("event_date", "")),
    )


def _select_pilot_candidates(candidates: list[dict[str, Any]], *, target_count: int) -> list[dict[str, Any]]:
    filtered = [item for item in candidates if item["raw_transcript_path"] or item["processed_case_dir"]]
    filtered.sort(key=_sort_key, reverse=True)

    selected: list[dict[str, Any]] = []
    per_ticker: dict[str, int] = {}
    seen_case_ids: set[str] = set()
    seen_events: set[tuple[str, str, str]] = set()
    for candidate in filtered:
        row = candidate["row"]
        case_id = str(candidate["case_id"] or "").strip()
        if not case_id or case_id in seen_case_ids:
            continue
        ticker = str(row.get("ticker", "")).strip()
        event_key = (
            ticker,
            str(row.get("quarter", "")).strip(),
            str(row.get("event_date", "")).strip(),
        )
        if event_key in seen_events:
            continue
        if per_ticker.get(ticker, 0) >= 2:
            continue
        selected.append(candidate)
        seen_case_ids.add(case_id)
        seen_events.add(event_key)
        per_ticker[ticker] = per_ticker.get(ticker, 0) + 1
        if len(selected) >= target_count:
            break
    return selected


def _reset_generated_outputs() -> None:
    layout = ensure_corpus_layout()
    generated_paths = [
        layout["manifests"] / "pilot_corpus_manifest.csv",
        layout["manifests"] / "pilot_corpus_manifest.jsonl",
        layout["reports"] / "pilot_corpus_summary.json",
    ]
    for path in generated_paths:
        if path.exists():
            path.unlink()

    for directory in (
        layout["raw_transcripts"],
        layout["processed_chunks"],
        layout["processed_evidence_objects"],
        layout["processed_alignments"],
    ):
        for path in directory.glob("*"):
            if path.is_file():
                path.unlink()

    retrieval_dir = layout["retrieval"] / "pilot_event_index"
    if retrieval_dir.exists():
        for path in retrieval_dir.glob("*"):
            if path.is_file():
                path.unlink()


def _copy_transcript_source(
    *,
    case_id: str,
    raw_transcript_path: Path | None,
    processed_case_dir: Path | None,
) -> Path:
    layout = ensure_corpus_layout()
    target_path = layout["raw_transcripts"] / f"{case_id}.txt"
    if raw_transcript_path is not None and raw_transcript_path.exists():
        shutil.copy2(raw_transcript_path, target_path)
        return target_path
    if processed_case_dir is not None and (processed_case_dir / "transcript.txt").exists():
        shutil.copy2(processed_case_dir / "transcript.txt", target_path)
        return target_path
    raise RuntimeError(f"No transcript source available for {case_id}")


def _is_youtube_url(url: str) -> bool:
    host = urlparse(url).netloc.casefold()
    return "youtube.com" in host or "youtu.be" in host


def _build_case_row(candidate: dict[str, Any]) -> CorpusCase:
    row = candidate["row"]
    official_row = candidate["official_row"]
    case_id = str(candidate["case_id"])
    processed_case_dir: Path | None = candidate["processed_case_dir"]
    raw_transcript_path: Path | None = candidate["raw_transcript_path"]
    transcript_copy_path = _copy_transcript_source(
        case_id=case_id,
        raw_transcript_path=raw_transcript_path,
        processed_case_dir=processed_case_dir,
    )

    source_url = str(row.get("source_url", "")).strip()
    official_source_url = str(official_row.get("official_source_url", "")).strip()
    transcript_url = official_source_url or source_url
    audio_url = source_url if _is_youtube_url(source_url) else ""
    video_url = source_url if _is_youtube_url(source_url) else ""
    transcript_parse_status = (
        "timed_segments_available"
        if processed_case_dir is not None and (processed_case_dir / "transcript.json").exists()
        else "raw_text_only"
    )
    audio_verified = bool(
        processed_case_dir is not None and (processed_case_dir / "audio_behavior_summary.json").exists()
    )
    video_verified = False

    provenance = {
        "generated_at": datetime.now(UTC).isoformat(),
        "call_manifest_path": candidate["call_manifest_path"],
        "official_manifest_path": candidate["official_manifest_path"],
        "call_manifest_row": row,
        "official_manifest_row": official_row,
        "raw_transcript_source": to_repo_relative(raw_transcript_path) if raw_transcript_path else "",
        "processed_case_dir": to_repo_relative(processed_case_dir) if processed_case_dir else "",
    }
    return CorpusCase(
        case_id=case_id,
        company=str(row.get("company", "")).strip(),
        ticker=str(row.get("ticker", "")).strip(),
        fiscal_period=str(row.get("quarter", "")).strip(),
        event_date=str(row.get("event_date", "")).strip(),
        transcript_url=transcript_url,
        transcript_local_path=to_repo_relative(transcript_copy_path),
        audio_url=audio_url,
        audio_local_path="",
        video_url=video_url,
        video_local_path="",
        transcript_verified=True,
        audio_verified=audio_verified,
        video_verified=video_verified,
        transcript_source_type=(
            "local_asr_transcript"
            if transcript_parse_status == "timed_segments_available"
            else "official_or_curated_transcript_text"
        ),
        audio_source_type=(
            "webcast_audio_from_youtube" if audio_url else ("derived_audio_review" if audio_verified else "")
        ),
        video_source_type="",
        transcript_parse_status=transcript_parse_status,
        audio_fetch_status="derived_outputs_available" if audio_verified else ("source_page_only" if audio_url else "not_available"),
        video_fetch_status="not_available",
        official_source_url=official_source_url,
        official_source_type=str(official_row.get("official_source_type", "")).strip(),
        source_url=source_url,
        origin_manifest_path=str(candidate["call_manifest_path"]),
        notes=_build_notes(row=row, official_row=official_row, audio_verified=audio_verified),
        provenance=provenance,
    )


def _build_notes(*, row: dict[str, str], official_row: dict[str, str], audio_verified: bool) -> str:
    notes = []
    manifest_notes = str(row.get("notes", "")).strip()
    official_notes = str(official_row.get("notes", "")).strip()
    if manifest_notes:
        notes.append(manifest_notes)
    if official_notes and official_notes != manifest_notes:
        notes.append(official_notes)
    if audio_verified:
        notes.append("Committed audio-derived review outputs exist, but the raw local audio file is not checked in under data/corpus.")
    return " ".join(notes).strip()


def _export_case_rows(rows: list[CorpusCase]) -> list[dict[str, str]]:
    manifest_rows: list[dict[str, str]] = []
    for case in rows:
        manifest_row = case.to_manifest_row()
        export_paths = export_case_artifacts(
            case_id=case.case_id,
            company=case.company,
            ticker=case.ticker,
            fiscal_period=case.fiscal_period,
            event_date=case.event_date,
            transcript_source_type=case.transcript_source_type,
            transcript_local_path=case.transcript_local_path,
            transcript_parse_status=case.transcript_parse_status,
            audio_verified=case.audio_verified,
            video_verified=case.video_verified,
            processed_case_dir=case.provenance.get("processed_case_dir", ""),
        )
        provenance = json.loads(manifest_row["provenance_json"])
        provenance["export_paths"] = export_paths
        manifest_row["provenance_json"] = json.dumps(provenance, sort_keys=True)
        manifest_rows.append(manifest_row)
    return manifest_rows


def _build_retrieval_records(manifest_rows: list[dict[str, str]]) -> list[RetrievalRecord]:
    records: list[RetrievalRecord] = []
    repo = repo_root()
    for row in manifest_rows:
        provenance = json.loads(str(row.get("provenance_json", "{}")))
        evidence_path = provenance.get("export_paths", {}).get("evidence_objects_path", "")
        if not evidence_path:
            continue
        for item in load_evidence_rows(repo / evidence_path):
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            if str(item.get("object_type", "")) not in {
                "event_chunk",
                "guidance_span",
                "qa_answer",
                "qa_question",
                "speaker_turn",
                "uncertainty_span",
                "skepticism_span",
            }:
                continue
            records.append(
                RetrievalRecord(
                    record_id=str(item.get("object_id", "")),
                    case_id=str(item.get("case_id", "")),
                    object_type=str(item.get("object_type", "")),
                    text=text,
                    metadata={
                        "ticker": str(item.get("ticker", "")),
                        "section": str(item.get("section", "")),
                        "speaker_role": str(item.get("speaker_role", "")),
                        "event_date": str(item.get("event_date", "")),
                    },
                )
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the transcript-first pilot corpus manifest and retrieval artifacts.")
    parser.add_argument("--target-count", type=int, default=20)
    parser.add_argument(
        "--embedding-provider",
        default="hashing",
        choices=["hashing", "sentence_transformers"],
    )
    args = parser.parse_args()

    layout = ensure_corpus_layout()
    _reset_generated_outputs()
    candidates = _load_candidates()
    selected = _select_pilot_candidates(candidates, target_count=max(1, args.target_count))
    case_rows = [_build_case_row(candidate) for candidate in selected]
    manifest_rows = _export_case_rows(case_rows)

    manifest_csv_path = layout["manifests"] / "pilot_corpus_manifest.csv"
    manifest_jsonl_path = layout["manifests"] / "pilot_corpus_manifest.jsonl"
    write_manifest_csv(manifest_csv_path, manifest_rows)
    write_manifest_jsonl(manifest_jsonl_path, manifest_rows)

    retrieval_records = _build_retrieval_records(manifest_rows)
    index_paths = write_retrieval_index(
        output_dir=layout["retrieval"] / "pilot_event_index",
        records=retrieval_records,
        provider=args.embedding_provider,
    )

    validation = build_manifest_validation_summary(manifest_rows)
    summary_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "selected_case_count": len(manifest_rows),
        "manifest_csv_path": to_repo_relative(manifest_csv_path),
        "manifest_jsonl_path": to_repo_relative(manifest_jsonl_path),
        "retrieval_index": {key: to_repo_relative(path) for key, path in index_paths.items()},
        "validation": validation,
        "selected_cases": [
            {
                "case_id": row["case_id"],
                "ticker": row["ticker"],
                "event_date": row["event_date"],
                "transcript_verified": row["transcript_verified"],
                "audio_verified": row["audio_verified"],
                "video_verified": row["video_verified"],
            }
            for row in manifest_rows
        ],
    }
    summary_path = layout["reports"] / "pilot_corpus_summary.json"
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    if validation["errors"]:
        raise SystemExit(
            "pilot corpus validation failed:\n- " + "\n- ".join(str(item) for item in validation["errors"])
        )

    print(f"Built pilot corpus with {len(manifest_rows)} cases")
    print(f"Manifest: {manifest_csv_path}")
    print(f"Index: {index_paths['summary_path']}")
    print(f"Validation warnings: {len(validation['warnings'])}")


if __name__ == "__main__":
    main()
