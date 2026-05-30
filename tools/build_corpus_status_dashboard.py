#!/usr/bin/env python3
"""Build first30 corpus status dashboard and preflight report."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DESKTOP_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
OUT_MD = ROOT / "reports" / "acquisition" / "corpus_status_dashboard.md"
OUT_JSON = ROOT / "reports" / "acquisition" / "corpus_status_dashboard.json"
PREFLIGHT_MD = ROOT / "reports" / "acquisition" / "next_ingestion_preflight.md"
COMPLETE_PREFLIGHT_MD = ROOT / "reports" / "acquisition" / "complete_first30_preflight.md"
COVERAGE_PREFLIGHT_MD = ROOT / "reports" / "acquisition" / "first30_coverage_preflight.md"

DASHBOARD_FIELDS = [
    "metric",
    "value",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _count_existing_paths(rows: list[dict[str, str]], field: str = "local_path") -> int:
    return sum(1 for row in rows if row.get(field) and Path(row[field]).exists())


def _first30_case_ids(candidates: list[dict[str, str]]) -> set[str]:
    return {row.get("case_id", "") for row in candidates if not row.get("candidate_id", "").startswith("control_")}


def build_dashboard(*, workspace: Path = DESKTOP_WORKSPACE, out_md: Path = OUT_MD, out_json: Path = OUT_JSON) -> dict[str, Any]:
    candidates = read_csv(ROOT / "data" / "acquisition" / "transcript_candidates_first30.csv")
    first30_ids = _first30_case_ids(candidates)
    ingestion = read_csv(ROOT / "data" / "acquisition" / "first30_transcript_ingestion_manifest.csv")
    active_ingestion_ids = {row.get("case_id", "") for row in ingestion if row.get("control_fixture") != "true"}
    matched_pairs = read_csv(ROOT / "data" / "acquisition" / "matched_pair_candidates.csv")
    pair_manifest = read_csv(ROOT / "data" / "acquisition" / "vz_2024_q4_pair_manifest.csv")
    audio_registry = read_csv(ROOT / "data" / "acquisition" / "audio_registry.csv")
    manual_audio = read_csv(ROOT / "data" / "corpus" / "manual_local_audio_registry.csv")
    transcripts = read_csv(ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv")
    parsed = read_csv(ROOT / "data" / "corpus" / "parsed_transcript_text_registry.csv")
    normalized = read_csv(ROOT / "data" / "corpus" / "normalized_transcript_manifest.csv")
    chunks = read_csv(ROOT / "data" / "acquisition" / "nyse_100_chunk_manifest.csv")
    evidence = read_csv(ROOT / "data" / "acquisition" / "nyse_100_evidence_objects_manifest.csv")
    retrieval = read_csv(ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv")
    asr_runs = read_csv(ROOT / "data" / "acquisition" / "asr_run_manifest.csv")
    asr_segments = read_csv(ROOT / "data" / "acquisition" / "asr_segment_manifest.csv")
    alignments = read_csv(ROOT / "data" / "acquisition" / "audio_transcript_alignment_manifest.csv")
    audio_objects = read_csv(ROOT / "data" / "retrieval" / "audio_objects_manifest.csv")
    eval_metrics = read_json(ROOT / "data" / "retrieval" / "first30_eval_metrics.json")
    training = read_csv(ROOT / "data" / "training" / "first30_training_readiness_manifest.csv")
    blockers = Counter()
    for row in ingestion:
        if row.get("control_fixture") == "true":
            continue
        if row.get("blocked_reason"):
            blockers[row["blocked_reason"]] += 1
    ingestion_blocked_cases = {row.get("case_id", "") for row in ingestion if row.get("blocked_reason")}
    for row in parsed:
        if row.get("case_id", "") in ingestion_blocked_cases:
            continue
        if row.get("text_parse_status") not in {"parsed", ""}:
            blockers[row.get("text_parse_status", "parse_blocked")] += 1
    transcript_registered_first30 = [row for row in transcripts if row.get("case_id") in first30_ids or row.get("case_id") in active_ingestion_ids or row.get("case_id") == "hd_2025_q4"]
    next_actions = []
    for row in ingestion:
        if row.get("control_fixture") == "true":
            continue
        if row.get("download_allowed") != "true" and len(next_actions) < 10:
            next_actions.append(f"Resolve or replace `{row.get('case_id')}`: {row.get('blocked_reason') or row.get('next_action')}")
    dashboard = {
        "first30_candidate_count": len(first30_ids),
        "candidate_rows_including_control": len(candidates),
        "official_direct_company_hosted_rows": sum(1 for row in ingestion if row.get("source_url_kind") == "official_direct"),
        "q4cdn_or_cloudfront_rows": sum(1 for row in ingestion if row.get("source_url_kind") == "official_ir_cdn_direct"),
        "approved_download_rows": sum(1 for row in ingestion if row.get("download_allowed") == "true"),
        "downloaded_transcript_count": _count_existing_paths(parsed, "raw_local_path"),
        "parsed_transcript_count": sum(1 for row in parsed if row.get("text_parse_status") == "parsed"),
        "registered_transcript_count": len(transcript_registered_first30),
        "registered_audio_count": len(audio_registry) or len(manual_audio),
        "matched_pair_count": len(matched_pairs),
        "verified_pair_manifest_rows": len(pair_manifest),
        "vz_2024_q4_status": pair_manifest[0].get("pair_status", "not_run") if pair_manifest else "not_run",
        "normalized_transcript_count": len(normalized),
        "chunk_count": len(chunks),
        "evidence_object_count": len(evidence),
        "retrieval_object_count": len(retrieval),
        "asr_ready_count": sum(1 for row in audio_registry if row.get("eval_allowed") == "true"),
        "asr_complete_count": sum(1 for row in asr_runs if row.get("status") == "complete"),
        "asr_segment_count": len(asr_segments),
        "audio_aligned_count": sum(1 for row in alignments if row.get("alignment_status") == "aligned"),
        "audio_object_count": len(audio_objects),
        "evaluated_rag": bool(eval_metrics.get("evaluated_rag", False)),
        "training_ready": any(row.get("status") == "READY" for row in training),
        "blockers_by_reason": dict(sorted(blockers.items())),
        "next_10_manual_actions": next_actions,
    }
    write_dashboard_md(dashboard, out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(dashboard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(workspace / "_audit" / "corpus_status_dashboard.csv", [{"metric": key, "value": json.dumps(value) if isinstance(value, (dict, list)) else value} for key, value in dashboard.items()], DASHBOARD_FIELDS)
    write_preflight(dashboard, PREFLIGHT_MD)
    write_preflight(dashboard, COMPLETE_PREFLIGHT_MD)
    write_preflight(dashboard, COVERAGE_PREFLIGHT_MD)
    return dashboard


def write_dashboard_md(dashboard: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Corpus Status Dashboard",
        "",
        f"- First30 candidate count: {dashboard['first30_candidate_count']}",
        f"- Approved/download rows: {dashboard['approved_download_rows']}",
        f"- Downloaded transcript count: {dashboard['downloaded_transcript_count']}",
        f"- Parsed transcript count: {dashboard['parsed_transcript_count']}",
        f"- Registered transcript count: {dashboard['registered_transcript_count']}",
        f"- Registered audio count: {dashboard['registered_audio_count']}",
        f"- Matched pair count: {dashboard['matched_pair_count']}",
        f"- Normalized transcript count: {dashboard['normalized_transcript_count']}",
        f"- Chunk/evidence/retrieval object count: {dashboard['chunk_count']} / {dashboard['evidence_object_count']} / {dashboard['retrieval_object_count']}",
        f"- ASR-ready and ASR-complete count: {dashboard['asr_ready_count']} / {dashboard['asr_complete_count']}",
        f"- Audio-aligned count: {dashboard['audio_aligned_count']}",
        f"- evaluated_rag={str(dashboard['evaluated_rag']).lower()}",
        f"- training_ready={str(dashboard['training_ready']).lower()}",
        "",
        "## Blockers By Reason",
        "",
    ]
    blockers = dashboard.get("blockers_by_reason") or {}
    if blockers:
        for reason, count in sorted(blockers.items()):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Next 10 Manual Actions", ""])
    actions = dashboard.get("next_10_manual_actions") or []
    lines.extend(f"- {action}" for action in actions) if actions else lines.append("- none")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_preflight(dashboard: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# First30 Coverage Preflight" if out_path == COVERAGE_PREFLIGHT_MD else "# Complete First30 Preflight" if out_path == COMPLETE_PREFLIGHT_MD else "# Next Ingestion Preflight",
        "",
        f"- First30 candidate count: {dashboard['first30_candidate_count']}",
        f"- Official/direct company-hosted rows: {dashboard['official_direct_company_hosted_rows']}",
        f"- Q4CDN rows: {dashboard['q4cdn_or_cloudfront_rows']}",
        f"- Registered transcripts/audio: {dashboard['registered_transcript_count']} / {dashboard['registered_audio_count']}",
        f"- Normalized transcripts: {dashboard['normalized_transcript_count']}",
        f"- Chunk/evidence/retrieval counts: {dashboard['chunk_count']} / {dashboard['evidence_object_count']} / {dashboard['retrieval_object_count']}",
        f"- ASR-ready and ASR-complete count: {dashboard['asr_ready_count']} / {dashboard['asr_complete_count']}",
        f"- Matched-pair count: {dashboard['matched_pair_count']}",
        f"- VZ_2024_Q4 status: {dashboard['vz_2024_q4_status']}",
        f"- Retrieval objects: {dashboard['retrieval_object_count']}",
        f"- evaluated_rag: {str(dashboard['evaluated_rag']).lower()}",
        f"- training_ready: {str(dashboard['training_ready']).lower()}",
        "",
        "## Top Blockers",
        "",
    ]
    blockers = dashboard.get("blockers_by_reason") or {}
    if blockers:
        for reason, count in sorted(blockers.items(), key=lambda item: (-item[1], item[0]))[:10]:
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Next 10 Exact Source Actions", ""])
    actions = dashboard.get("next_10_manual_actions") or []
    if actions:
        lines.extend(f"- {action}" for action in actions)
    else:
        lines.append("- none")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first30 corpus status dashboard.")
    parser.add_argument("--workspace", type=Path, default=DESKTOP_WORKSPACE)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    args = parser.parse_args(argv)
    dashboard = build_dashboard(workspace=args.workspace, out_md=args.out_md, out_json=args.out_json)
    print(json.dumps(dashboard, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
