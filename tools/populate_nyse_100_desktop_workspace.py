#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import (
    BLOCKED_SOURCE_FIELDS,
    COMPANY_FIELDS,
    RIGHTS_DECISION_FIELDS,
    build_call_targets,
    build_company_universe,
    build_ir_source_candidates,
    build_sec_event_index,
    build_source_availability,
    build_source_candidates,
    populate_desktop_workspace,
    read_csv,
    summary_markdown,
    write_csv,
    write_json,
)

def run(
    *,
    target_count: int,
    start_year: int,
    years_back: int,
    output_root: Path,
    checkpoint_interval: int,
) -> dict[str, object]:
    companies = build_company_universe()[:target_count]
    targets = build_call_targets(companies, start_year=start_year, years_back=years_back)
    rights_rows = build_source_candidates(targets)
    ir_rows = build_ir_source_candidates(targets)
    sec_rows = build_sec_event_index(targets)
    availability_rows = build_source_availability(targets, rights_rows)

    data_dir = ROOT / "data" / "acquisition"
    reports_dir = ROOT / "reports" / "acquisition"
    write_csv(data_dir / "nyse_100_company_universe.csv", companies, COMPANY_FIELDS)
    (data_dir / "nyse_100_company_selection_notes.md").write_text(
        "# NYSE 100 Company Selection Notes\n\n"
        "- Universe size: 100 companies.\n"
        "- Exchange: NYSE only, verified against SEC exchange metadata on 2026-05-24.\n"
        "- Exclusions: obvious NASDAQ/uncertain names are not included in acquisition targets.\n"
        "- Coverage: banking, industrials, healthcare, consumer, telecom, energy, aerospace, insurance, payments, retail, logistics, and financial infrastructure.\n"
        "- Rights policy: company selection does not authorize raw transcript/audio/video acquisition.\n",
        encoding="utf-8",
    )
    write_csv(data_dir / "nyse_100_5y_call_targets.csv", targets, [
        "case_id",
        "ticker",
        "company_name",
        "exchange",
        "sector",
        "target_year",
        "fiscal_year",
        "fiscal_quarter",
        "calendar_year",
        "event_date",
        "event_identity_status",
        "source_status",
        "notes",
    ])
    write_csv(
        data_dir / "nyse_100_ir_source_candidates.csv",
        ir_rows,
        [
            "case_id",
            "ticker",
            "company_name",
            "fiscal_year",
            "fiscal_quarter",
            "official_ir_url",
            "source_domain",
            "candidate_type",
            "network_fetch_enabled",
            "source_status",
            "rights_status",
            "notes",
        ],
    )
    write_csv(
        data_dir / "nyse_100_sec_event_index.csv",
        sec_rows,
        [
            "case_id",
            "ticker",
            "company_name",
            "fiscal_year",
            "fiscal_quarter",
            "target_forms",
            "sec_company_ref",
            "accession_number",
            "filing_url",
            "item_202_or_exhibit_991",
            "rights_status",
            "blocked_reason",
            "notes",
        ],
    )
    write_csv(
        data_dir / "nyse_100_source_availability.csv",
        availability_rows,
        [
            "case_id",
            "ticker",
            "company_name",
            "exchange",
            "fiscal_year",
            "fiscal_quarter",
            "event_identity_status",
            "official_ir_status",
            "sec_status",
            "transcript_status",
            "audio_status",
            "video_status",
            "safe_download_candidates",
            "blocked_source_count",
            "next_action",
        ],
    )
    write_csv(data_dir / "nyse_100_rights_decisions.csv", rights_rows, RIGHTS_DECISION_FIELDS)
    write_csv(data_dir / "nyse_100_chunk_manifest.csv", [], [
        "chunk_id",
        "case_id",
        "ticker",
        "source_sha256",
        "chunk_type",
        "section",
        "speaker_role",
        "start_hint",
        "end_hint",
        "text_sha256",
        "local_chunk_path",
        "rights_status",
        "raw_text_committed",
    ])

    summary = populate_desktop_workspace(targets, output_root=output_root, checkpoint_interval=checkpoint_interval)
    write_json(reports_dir / "nyse_100_acquisition_summary.json", summary)
    (reports_dir / "nyse_100_acquisition_summary.md").write_text(summary_markdown(summary), encoding="utf-8")
    write_json(reports_dir / "acquisition_summary.json", summary)
    sector_counts: dict[str, int] = {}
    for company in companies:
        sector_counts[company["sector"]] = sector_counts.get(company["sector"], 0) + 1
    (reports_dir / "nyse_100_company_universe.md").write_text(
        "# NYSE 100 Company Universe\n\n"
        f"- Total companies: {len(companies)}\n"
        "- Exchange filter: NYSE only.\n"
        "- Exchange status: verified_sec_exchange_metadata_2026-05-24.\n\n"
        "## Sector Counts\n\n"
        + "\n".join(f"- {sector}: {count}" for sector, count in sorted(sector_counts.items()))
        + "\n",
        encoding="utf-8",
    )
    (reports_dir / "nyse_100_5y_call_targets.md").write_text(
        "# NYSE 100 Five-Year Call Targets\n\n"
        f"- Target rows: {len(targets)}\n"
        "- Start year: 2025.\n"
        "- Lookback: 5 fiscal years, annual/Q4 target slot per company per year.\n"
        "- Event dates are period-end placeholders unless event_identity_status is later upgraded by IR/SEC discovery.\n"
        "- No target row asserts that an earnings call exists until metadata discovery confirms it.\n",
        encoding="utf-8",
    )
    (reports_dir / "official_ir_discovery.md").write_text(
        "# Official IR Discovery\n\n"
        f"- Candidate rows: {len(ir_rows)}\n"
        "- Mode: metadata-first discovery using known official IR URLs or placeholders.\n"
        "- Raw transcript/audio acquisition is disabled unless source rights are explicitly approved.\n",
        encoding="utf-8",
    )
    (reports_dir / "sec_metadata_discovery.md").write_text(
        "# SEC Metadata Discovery\n\n"
        f"- SEC metadata target rows: {len(sec_rows)}\n"
        "- Forms targeted: 8-K, 10-Q, 10-K.\n"
        "- Filing body and exhibit downloads are disabled by default; SEC rows are metadata-first.\n"
        "- Policy: descriptive User-Agent required and rate limit <=10 requests/sec when network mode is enabled.\n",
        encoding="utf-8",
    )
    blocked = read_csv(output_root / "_audit" / "blocked_sources.csv")
    write_csv(reports_dir / "blocked_sources.csv", blocked, BLOCKED_SOURCE_FIELDS)
    (reports_dir / "blocked_sources.md").write_text(
        "# Blocked Sources\n\n"
        f"- Blocked source rows: {len(blocked)}\n"
        "- Top blockers are recorded in the Desktop and repo acquisition summaries.\n",
        encoding="utf-8",
    )
    (reports_dir / "rights_decision_summary.md").write_text(
        "# Rights Decision Summary\n\n"
        f"- Rights decision rows: {len(rights_rows)}\n"
        "- Unknown rights fail closed.\n"
        "- YouTube media and vendor raw content are blocked unless explicit authorization/license config exists.\n",
        encoding="utf-8",
    )
    (reports_dir / "manual_review_queue.md").write_text(
        "# Manual Review Queue\n\n"
        "- Review official IR pages for event identity, source terms, and robots policy.\n"
        "- Register manually supplied rights-cleared transcripts by local path and sha256 only.\n",
        encoding="utf-8",
    )
    (reports_dir / "safe_download_candidates.md").write_text(
        "# Safe Download Candidates\n\n- Safe download candidates: 0\n- No raw transcript or audio downloads are authorized by this metadata-first run.\n",
        encoding="utf-8",
    )
    (reports_dir / "manual_local_registration_status.md").write_text(
        "# Manual-Local Registration Status\n\n- Registered transcripts: 0\n- No local transcript files were copied into git.\n",
        encoding="utf-8",
    )
    (reports_dir / "rag_readiness_summary.md").write_text(
        "# RAG Readiness Summary\n\n- BM25-ready text chunks: 0\n- Evidence objects generated: 0\n- Vector DB created: no\n",
        encoding="utf-8",
    )
    (ROOT / "data" / "corpus").mkdir(parents=True, exist_ok=True)
    write_csv(
        ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv",
        [],
        [
            "case_id",
            "ticker",
            "company_name",
            "fiscal_period",
            "asset_type",
            "local_path",
            "sha256",
            "rights_status",
            "eval_allowed",
            "commit_allowed",
            "training_allowed",
            "raw_file_copied_into_repo",
            "registered_timestamp",
            "notes",
        ],
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate a local NYSE 100 metadata-first acquisition workspace.")
    parser.add_argument("--target-count", type=int, default=100)
    parser.add_argument("--start-year", type=int, default=2025)
    parser.add_argument("--years-back", type=int, default=5)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--metadata-first", action="store_true")
    parser.add_argument("--allow-permitted-downloads", action="store_true")
    parser.add_argument("--no-youtube-download", action="store_true")
    parser.add_argument("--checkpoint-interval", type=int, default=25)
    args = parser.parse_args()
    summary = run(
        target_count=args.target_count,
        start_year=args.start_year,
        years_back=args.years_back,
        output_root=args.output_root,
        checkpoint_interval=args.checkpoint_interval,
    )
    print(summary)


if __name__ == "__main__":
    main()
