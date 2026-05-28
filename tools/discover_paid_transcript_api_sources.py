#!/usr/bin/env python3
"""Build metadata-only source candidates for paid transcript API providers."""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import os
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.source_adapters import SOURCE_CANDIDATE_FIELDS, candidate_to_csv_row, normalize_candidate, source_domain_for_url

DEFAULT_CONFIG = ROOT / "configs" / "transcript_api_providers.example.yml"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_paid_transcript_api_source_candidates.csv"
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "paid_transcript_api_discovery.md"


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"providers": []}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"providers": []}


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_CANDIDATE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _provider_candidates(provider: dict[str, Any]) -> list[dict[str, Any]]:
    cases = provider.get("candidate_cases") or [{}]
    rows: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        base_url = str(provider.get("base_url", "")).strip()
        rows.append(
            {
                "case_id": case.get("case_id", ""),
                "ticker": case.get("ticker", ""),
                "company_name": case.get("company_name", ""),
                "fiscal_period": case.get("fiscal_period", ""),
                "event_date": case.get("event_date", ""),
                "source_type": "paid_transcript_api",
                "source_name": provider.get("provider_name", ""),
                "source_domain": source_domain_for_url(base_url),
                "source_url": base_url,
                "discovered_from_url": base_url,
                "discovery_method": "paid_api_metadata_scaffold",
                "candidate_kind": "transcript",
                "rights_status": "licensed_vendor_metadata_only",
                "download_allowed": False,
                "approval_required": True,
                "raw_text_committed": False,
                "license_config_ref": provider.get("license_config_ref", ""),
                "robots_allowed": False,
                "paywall_status": "api_key_required",
                "confidence": 0.4,
                "notes": "Metadata-only paid API candidate; raw transcript retrieval is not implemented in this layer.",
            }
        )
    return rows


def write_report(path: Path, *, summary: dict[str, Any], statuses: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Paid Transcript API Discovery",
        "",
        f"- Created at: {datetime.now(UTC).replace(microsecond=0).isoformat()}",
        f"- Providers checked: {summary['providers_checked']}",
        f"- Providers skipped: {summary['providers_skipped']}",
        f"- Providers blocked: {summary['providers_blocked']}",
        f"- Candidates written: {summary['candidates_written']}",
        "- Provider document fetch performed: false",
        "- Provider document storage performed: false",
        "- Downloads allowed by discovery: false",
        "",
        "## Provider Status",
    ]
    lines.extend(f"- {status}" for status in statuses)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_discovery(*, config_path: Path = DEFAULT_CONFIG, out_csv: Path = DEFAULT_OUT, report_path: Path = DEFAULT_REPORT) -> dict[str, Any]:
    config = read_config(config_path)
    providers = [provider for provider in config.get("providers", []) if isinstance(provider, dict)]
    statuses: list[str] = []
    candidates: list[dict[str, str]] = []
    skipped = 0
    blocked = 0
    for provider in providers:
        name = str(provider.get("provider_name", "unknown_provider"))
        if not bool(provider.get("enabled", False)):
            skipped += 1
            statuses.append(f"{name}: skipped disabled")
            continue
        api_key_env_var = str(provider.get("api_key_env_var", "")).strip()
        if not api_key_env_var or not os.environ.get(api_key_env_var):
            skipped += 1
            statuses.append(f"{name}: skipped missing api key")
            continue
        if not str(provider.get("license_config_ref", "")).strip():
            blocked += 1
            statuses.append(f"{name}: blocked missing license_config_ref")
            continue
        provider_rows = [candidate_to_csv_row(normalize_candidate(row)) for row in _provider_candidates(provider)]
        candidates.extend(provider_rows)
        statuses.append(f"{name}: metadata-only candidates generated")
    write_csv(out_csv, candidates)
    summary = {
        "providers_checked": len(providers),
        "providers_skipped": skipped,
        "providers_blocked": blocked,
        "candidates_written": len(candidates),
    }
    write_report(report_path, summary=summary, statuses=statuses)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_discovery(config_path=args.config, out_csv=args.out_csv, report_path=args.report_path)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
