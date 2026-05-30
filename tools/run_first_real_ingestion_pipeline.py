#!/usr/bin/env python3
"""Run first-real NYSE ingestion from manual-local files and direct resolved assets."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import read_csv, resolve_official_ir_event_rows, write_csv  # noqa: E402
from signal_engine.acquisition.direct_asset_detector import detect_direct_asset  # noqa: E402
from tools.build_event_chunks import build_event_chunks  # noqa: E402
from tools.build_local_retrieval_index import build_index  # noqa: E402
from tools.build_user_authorized_audio_rag import build_user_authorized_audio_rag  # noqa: E402
from tools.discover_desktop_transcript_audio_assets import discover_desktop_assets  # noqa: E402
from tools.download_resolved_earnings_assets import download_resolved_assets  # noqa: E402
from tools.export_retrieval_objects import export_retrieval_objects  # noqa: E402
from tools.normalize_registered_transcripts import normalize_registered_transcripts  # noqa: E402
from tools.register_resolved_desktop_assets import register_resolved_assets  # noqa: E402
from tools.run_nyse100_asset_resolution_pipeline import _default_provider, _default_sec, run_asset_resolution_pipeline  # noqa: E402
from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE, DOWNLOAD_LOG_FIELDS  # noqa: E402

DEFAULT_ACQUISITION_DIR = ROOT / "data" / "acquisition"
DEFAULT_CORPUS_DIR = ROOT / "data" / "corpus"
DEFAULT_RETRIEVAL_DIR = ROOT / "data" / "retrieval"
DEFAULT_LOCAL_INDEX_DIR = ROOT / ".local" / "signal_engine" / "retrieval" / "indexes" / "nyse100_bm25"


def _official_event_default(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return resolve_official_ir_event_rows(rows, max_pages_per_row=3, per_domain_delay_sec=0.25)


def _combine_logs(paths: list[Path], out_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        for row in read_csv(path):
            rows.append({field: row.get(field, "") for field in DOWNLOAD_LOG_FIELDS})
    write_csv(out_path, rows, DOWNLOAD_LOG_FIELDS)
    return rows


def _report_dirs(acquisition_dir: Path) -> tuple[Path, Path]:
    if acquisition_dir.resolve() == DEFAULT_ACQUISITION_DIR.resolve():
        return ROOT / "reports" / "acquisition", ROOT / "reports" / "retrieval"
    repo_root = acquisition_dir.parent.parent
    return repo_root / "reports" / "acquisition", repo_root / "reports" / "retrieval"


def _write_preflight(
    path: Path,
    *,
    acquisition_dir: Path,
    workspace: Path,
    manual_summary: dict[str, Any],
    provider_status: dict[str, str],
) -> None:
    source_rows = read_csv(acquisition_dir / "nyse_100_source_rights_review_queue.csv")
    ranked_rows = read_csv(acquisition_dir / "nyse_100_ranked_asset_candidates.csv")
    transcript_registry = read_csv(acquisition_dir.parent / "corpus" / "manual_local_transcript_registry.csv")
    audio_registry = read_csv(acquisition_dir.parent / "corpus" / "manual_local_audio_registry.csv")
    chunks = read_csv(acquisition_dir / "nyse_100_chunk_manifest.csv")
    blockers = Counter(row.get("blocked_reason", "") for row in ranked_rows if row.get("blocked_reason"))
    by_type = Counter(row.get("asset_type", "") for row in ranked_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First Real Ingestion Preflight",
        "",
        f"- Source rows available: {len(source_rows)}",
        f"- Landing page rows: {by_type.get('landing_page', 0)}",
        f"- Direct asset candidates: {sum(by_type.get(k, 0) for k in ('transcript_text', 'transcript_html', 'transcript_pdf', 'audio_mp3', 'audio_m4a', 'audio_wav'))}",
        f"- Desktop transcript files present: {manual_summary['transcript_files']}",
        f"- Desktop audio files present: {manual_summary['audio_files']}",
        f"- Manual-local candidates: {manual_summary['files_found']}",
        f"- Registered transcripts: {len(transcript_registry)}",
        f"- Registered audio: {len(audio_registry)}",
        f"- Current chunk/RAG rows: {len(chunks)}",
        f"- Desktop workspace: `{workspace}`",
        "",
        "## Provider Keys",
    ]
    lines.extend(f"- {name}: {status}" for name, status in provider_status.items())
    lines.append("")
    lines.append("## Top Blockers")
    lines.extend(f"- {reason}: {count}" for reason, count in blockers.most_common(10))
    if not blockers:
        lines.append("- none")
    lines.append("")
    lines.append("## Fastest Route")
    if manual_summary["files_found"]:
        lines.append("- Manual-local Desktop files are present; register and process them first.")
    else:
        lines.append("- No Desktop transcript/audio files were found; use official direct assets or add lawful manual-local files.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _provider_status() -> dict[str, str]:
    import os

    return {
        "EARNINGSCALL_API_KEY": "present" if os.environ.get("EARNINGSCALL_API_KEY") else "missing",
        "FMP_API_KEY": "present" if os.environ.get("FMP_API_KEY") else "missing",
        "API_NINJAS_KEY": "present" if os.environ.get("API_NINJAS_KEY") else "missing",
        "FINNHUB_API_KEY": "present" if os.environ.get("FINNHUB_API_KEY") else "missing",
        "QUARTR_API_KEY": "present" if os.environ.get("QUARTR_API_KEY") else "missing",
        "SEC_USER_AGENT": "present" if os.environ.get("SEC_USER_AGENT") else "missing",
    }


def _usable_pairs(transcript_rows: list[dict[str, str]], audio_rows: list[dict[str, str]]) -> int:
    transcript_cases = {row.get("case_id", "") for row in transcript_rows}
    audio_cases = {row.get("case_id", "") for row in audio_rows}
    return len((transcript_cases & audio_cases) - {""})


def run_first_real_ingestion_pipeline(
    *,
    workspace: Path = DEFAULT_WORKSPACE,
    acquisition_dir: Path = DEFAULT_ACQUISITION_DIR,
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    retrieval_dir: Path = DEFAULT_RETRIEVAL_DIR,
    local_index_dir: Path = DEFAULT_LOCAL_INDEX_DIR,
    target_pairs: int = 100,
    start_year: int = 2025,
    years_back: int = 5,
    expand_until_exhausted: bool = False,
    max_workers: int = 1,
    official_resolver: Callable[[list[dict[str, str]]], list[dict[str, str]]] = _official_event_default,
    sec_resolver: Callable[[list[dict[str, str]]], list[dict[str, str]]] = _default_sec,
    provider_resolver: Callable[[list[dict[str, str]]], list[dict[str, str]]] = _default_provider,
    direct_detector: Callable[[dict[str, str]], dict[str, str]] = detect_direct_asset,
) -> dict[str, Any]:
    acquisition_report_dir, retrieval_report_dir = _report_dirs(acquisition_dir)
    manual_log = workspace / "_audit" / "manual_local_desktop_asset_discovery.csv"
    manual_summary = discover_desktop_assets(workspace=workspace, out_path=manual_log)
    _write_preflight(
        acquisition_report_dir / "first_real_ingestion_preflight.md",
        acquisition_dir=acquisition_dir,
        workspace=workspace,
        manual_summary=manual_summary,
        provider_status=_provider_status(),
    )
    asset_summary = run_asset_resolution_pipeline(
        acquisition_dir=acquisition_dir,
        workspace=workspace,
        target_pairs=target_pairs,
        start_year=start_year,
        years_back=years_back,
        expand_until_exhausted=expand_until_exhausted,
        max_workers=max_workers,
        official_resolver=official_resolver,
        sec_resolver=sec_resolver,
        provider_resolver=provider_resolver,
        direct_detector=direct_detector,
    )
    download_summary = download_resolved_assets(
        manifest=acquisition_dir / "nyse_100_user_authorized_permitted_downloads.csv",
        workspace=workspace,
    )
    combined_log = workspace / "_audit" / "first_real_combined_download_log.csv"
    combined_rows = _combine_logs([manual_log, workspace / "_audit" / "resolved_download_log.csv"], combined_log)
    transcript_registry = corpus_dir / "manual_local_transcript_registry.csv"
    audio_registry = corpus_dir / "manual_local_audio_registry.csv"
    registration_summary = register_resolved_assets(
        workspace=workspace,
        download_log=combined_log,
        transcript_out=transcript_registry,
        audio_out=audio_registry,
    )
    normalization_summary = normalize_registered_transcripts(
        registry_path=transcript_registry,
        workspace=workspace,
        out_path=corpus_dir / "normalized_transcript_manifest.csv",
    )
    chunk_summary = build_event_chunks(
        registry_path=transcript_registry,
        workspace=workspace,
        out_path=acquisition_dir / "nyse_100_chunk_manifest.csv",
        evidence_out=acquisition_dir / "nyse_100_evidence_objects_manifest.csv",
    )
    retrieval_summary = export_retrieval_objects(
        chunk_manifest=acquisition_dir / "nyse_100_chunk_manifest.csv",
        out_path=retrieval_dir / "retrieval_objects_manifest.csv",
    )
    index_summary = build_index(objects_path=retrieval_dir / "retrieval_objects_manifest.csv", out_dir=local_index_dir)
    audio_summary = build_user_authorized_audio_rag(
        registry_path=audio_registry,
        workspace=workspace,
        out_path=acquisition_dir / "nyse_100_audio_rag_manifest.csv",
    )
    transcript_rows = read_csv(transcript_registry)
    audio_rows = read_csv(audio_registry)
    ranked = read_csv(acquisition_dir / "nyse_100_ranked_asset_candidates.csv")
    download_log_rows = read_csv(workspace / "_audit" / "resolved_download_log.csv")
    by_type = Counter(row.get("asset_type", "") for row in ranked)
    blockers = Counter(row.get("blocked_reason", "") for row in ranked if row.get("blocked_reason"))
    blockers.update(row.get("blocked_reason", "") for row in download_log_rows if row.get("blocked_reason"))
    domains = Counter(row.get("asset_url_domain", "") for row in ranked if row.get("asset_url_domain"))
    summary: dict[str, Any] = {
        "companies_scanned": asset_summary.get("companies_scanned", 0),
        "calls_scanned": asset_summary.get("calls_scanned", 0),
        "extra_nyse_companies_scanned": 0,
        "manual_local_files_found": manual_summary["files_found"],
        "manual_local_transcript_files": manual_summary["transcript_files"],
        "manual_local_audio_files": manual_summary["audio_files"],
        "transcript_asset_candidates_found": sum(by_type.get(k, 0) for k in ("transcript_text", "transcript_pdf", "transcript_html")),
        "audio_asset_candidates_found": sum(by_type.get(k, 0) for k in ("audio_mp3", "audio_m4a", "audio_wav")),
        "transcript_downloads_attempted": download_summary["transcript_attempts"],
        "transcript_downloads_succeeded": download_summary["transcript_successes"],
        "audio_downloads_attempted": download_summary["audio_attempts"],
        "audio_downloads_succeeded": download_summary["audio_successes"],
        "registered_transcripts": registration_summary["registered_transcripts"],
        "registered_audio": registration_summary["registered_audio"],
        "normalized_transcripts": normalization_summary["normalized_transcripts"],
        "chunks": chunk_summary["transcript_chunks"],
        "evidence_objects": chunk_summary["evidence_objects"],
        "retrieval_objects": retrieval_summary["retrieval_objects"],
        "rag_ready_calls": chunk_summary["rag_ready_calls"],
        "audio_rag_records": audio_summary["audio_rag_records"],
        "audio_asr_ready_calls": audio_summary["audio_rag_records"],
        "usable_pairs": _usable_pairs(transcript_rows, audio_rows),
        "combined_download_log_rows": len(combined_rows),
        "top_domains": domains.most_common(10),
        "top_blockers": blockers.most_common(10),
        "local_bm25_documents": index_summary["document_count"],
        "manual_actions": [
            "Add lawful manual-local transcript/audio files under the Desktop workspace when official direct assets are unavailable.",
            "Review official IR event pages for exact period/date transcript or replay links.",
            "Configure provider API keys and license_config_ref before any vendor raw ingestion.",
            "Do not use YouTube media unless a written authorization reference is present.",
        ],
    }
    _write_final_reports(summary, acquisition_report_dir, retrieval_report_dir, workspace)
    return summary


def _write_final_reports(summary: dict[str, Any], acquisition_report_dir: Path, retrieval_report_dir: Path, workspace: Path) -> None:
    acquisition_report_dir.mkdir(parents=True, exist_ok=True)
    retrieval_report_dir.mkdir(parents=True, exist_ok=True)
    workspace_audit = workspace / "_audit"
    workspace_audit.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Final First Real Ingestion Status",
        "",
        f"- Companies scanned: {summary['companies_scanned']}",
        f"- Calls scanned: {summary['calls_scanned']}",
        f"- Extra NYSE companies scanned beyond first 100: {summary['extra_nyse_companies_scanned']}",
        f"- Manual-local files found: {summary['manual_local_files_found']}",
        f"- Transcript asset candidates found: {summary['transcript_asset_candidates_found']}",
        f"- Audio asset candidates found: {summary['audio_asset_candidates_found']}",
        f"- Transcript downloads attempted/succeeded: {summary['transcript_downloads_attempted']}/{summary['transcript_downloads_succeeded']}",
        f"- Audio downloads attempted/succeeded: {summary['audio_downloads_attempted']}/{summary['audio_downloads_succeeded']}",
        f"- Registered transcripts: {summary['registered_transcripts']}",
        f"- Registered audio: {summary['registered_audio']}",
        f"- Normalized transcripts: {summary['normalized_transcripts']}",
        f"- Chunks: {summary['chunks']}",
        f"- Evidence objects: {summary['evidence_objects']}",
        f"- Retrieval objects: {summary['retrieval_objects']}",
        f"- RAG-ready calls: {summary['rag_ready_calls']}",
        f"- Audio ASR-ready calls: {summary['audio_asr_ready_calls']}",
        f"- Usable transcript/audio pairs: {summary['usable_pairs']}",
        "",
        "## Top Domains",
    ]
    lines.extend(f"- {domain}: {count}" for domain, count in summary["top_domains"])
    if not summary["top_domains"]:
        lines.append("- none")
    lines.append("")
    lines.append("## Top Blockers")
    lines.extend(f"- {reason}: {count}" for reason, count in summary["top_blockers"])
    if not summary["top_blockers"]:
        lines.append("- none")
    lines.append("")
    lines.append("## Exact Next Manual Actions")
    lines.extend(f"- {action}" for action in summary["manual_actions"])
    text = "\n".join(lines) + "\n"
    (acquisition_report_dir / "final_first_real_ingestion_status.md").write_text(text, encoding="utf-8")
    (workspace_audit / "final_first_real_ingestion_status.md").write_text(text, encoding="utf-8")
    (workspace_audit / "final_first_real_ingestion_status.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (retrieval_report_dir / "retrieval_eval_summary.md").write_text(
        "# Retrieval Eval Summary\n\n"
        f"- Retrieval objects: {summary['retrieval_objects']}\n"
        "- Evaluation queries run: 0\n"
        "- Raw text returned: false\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run first real NYSE transcript/audio ingestion pipeline.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--target-pairs", type=int, default=100)
    parser.add_argument("--start-year", type=int, default=2025)
    parser.add_argument("--years-back", type=int, default=5)
    parser.add_argument("--expand-until-exhausted", action="store_true")
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            run_first_real_ingestion_pipeline(
                workspace=args.workspace,
                target_pairs=args.target_pairs,
                start_year=args.start_year,
                years_back=args.years_back,
                expand_until_exhausted=args.expand_until_exhausted,
                max_workers=args.max_workers,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
