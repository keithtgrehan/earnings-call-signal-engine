#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

import yaml

FIELDS = [
    "rank",
    "case_id",
    "ticker",
    "company_name",
    "fiscal_period",
    "local_path",
    "source_sha256",
    "file_size",
    "extension",
    "candidate_reason",
    "source_url",
    "rights_tier",
    "eval_allowed",
    "training_allowed",
    "commit_allowed",
    "manual_action",
    "registration_ready",
]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_nyse30(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {}
    return {str(row.get("ticker", "")).upper(): str(row.get("company_name", "")) for row in rows if isinstance(row, dict)}


def _load_nyse100(path: Path) -> set[str]:
    rows = _load_csv(path)
    tickers = {str(row.get("ticker_symbol") or row.get("ticker") or "").upper() for row in rows}
    cases = {str(row.get("case_id", "")).lower() for row in rows}
    return {value for value in tickers | cases if value}


def _infer_ticker(row: dict[str, str]) -> str:
    ticker = str(row.get("ticker", "")).upper()
    if ticker:
        return ticker
    case_id = str(row.get("case_id", ""))
    match = re.match(r"([a-z]{1,6})_", case_id, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _period_score(period: str) -> tuple[int, int]:
    match = re.search(r"(20\d{2})[_ -]?Q([1-4])", period, flags=re.IGNORECASE)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def _bool_text(value: str | None) -> str:
    return "true" if str(value or "").strip().lower() in {"1", "true", "yes", "y"} else "false"


def _registration_ready(row: dict[str, str], source_sha256: str) -> bool:
    rights_tier = str(row.get("rights_tier", "")).strip().lower()
    source_url = str(row.get("source_url", "")).strip()
    if not source_url or not source_sha256.startswith("sha256:"):
        return False
    if rights_tier in {"", "unknown", "restricted"}:
        return False
    return True


def _path_kind(path: Path) -> tuple[int, str]:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if "raw" in parts and name.startswith("transcript"):
        return (0, "raw transcript file")
    if "clean" in parts and "transcript" in name:
        return (1, "clean transcript file")
    if "transcript" in name:
        return (2, "transcript-named file")
    return (3, "possible transcript file")


def _extension_score(path: Path) -> int:
    return {".txt": 0, ".md": 1, ".pdf": 2}.get(path.suffix.lower(), 3)


def _size_score(size: int) -> int:
    if 20_000 <= size <= 250_000:
        return 0
    if 8_000 <= size < 20_000 or 250_000 < size <= 500_000:
        return 1
    return 2


def _has_rights_conflict(row: dict[str, str]) -> bool:
    rights_tier = str(row.get("rights_tier", "unknown")).strip().lower()
    any_allowed = any(_bool_text(row.get(field)) == "true" for field in ("eval_allowed", "training_allowed", "commit_allowed"))
    return rights_tier in {"", "unknown", "restricted"} and any_allowed


def _reason(
    *,
    nyse30: bool,
    nyse100: bool,
    path_kind: str,
    size: int,
    extension: str,
    source_url: str,
    rights_tier: str,
    rights_conflict: bool,
) -> str:
    parts: list[str] = []
    if nyse30:
        parts.append("NYSE 30 target")
    elif nyse100:
        parts.append("NYSE 100 source-status candidate")
    parts.append(path_kind)
    parts.append(f"{extension or 'no-extension'} file")
    parts.append("plausible full-transcript size" if _size_score(size) == 0 else "size needs human check")
    parts.append("source_url present" if source_url else "source_url missing")
    parts.append(f"rights_tier={rights_tier or 'unknown'}")
    if rights_conflict:
        parts.append("rights/status conflict: keep blocked")
    return "; ".join(parts)


def build_top30(
    *,
    discovery_path: Path,
    batch_path: Path,
    nyse30_path: Path,
    nyse100_path: Path,
    limit: int = 30,
) -> list[dict[str, str]]:
    discovery_by_path = {str(row.get("path_ref", "")): row for row in _load_jsonl(discovery_path)}
    batch_rows = _load_csv(batch_path)
    nyse30 = _load_nyse30(nyse30_path)
    nyse100 = _load_nyse100(nyse100_path)

    ranked: list[tuple[tuple[Any, ...], dict[str, str]]] = []
    for row in batch_rows:
        local_path = str(row.get("local_path", ""))
        path = Path(local_path)
        discovery = discovery_by_path.get(local_path, {})
        ticker = _infer_ticker(row)
        case_id = str(row.get("case_id", "")).lower()
        size = int(discovery.get("size_bytes", 0) or 0)
        source_sha256 = str(discovery.get("sha256", ""))
        path_rank, path_kind = _path_kind(path)
        nyse30_hit = ticker in nyse30
        nyse100_hit = ticker in nyse100 or case_id in nyse100
        rights_tier = str(row.get("rights_tier") or "unknown")
        source_url = str(row.get("source_url", ""))
        rights_conflict = _has_rights_conflict(row)
        registration_ready = _registration_ready(row, source_sha256) and not rights_conflict
        period = str(row.get("fiscal_period") or "")
        year, quarter = _period_score(period)
        score = (
            0 if path_rank <= 2 else 1,
            0 if nyse30_hit else 1,
            0 if nyse100_hit else 1,
            0 if ticker and case_id else 1,
            -year,
            -quarter,
            _extension_score(path),
            _size_score(size),
            0 if source_url else 1,
            1 if rights_conflict else 0,
            path_rank,
            local_path,
        )
        output = {
            "rank": "0",
            "case_id": case_id,
            "ticker": ticker,
            "company_name": str(row.get("company_name") or nyse30.get(ticker, "")),
            "fiscal_period": period,
            "local_path": local_path,
            "source_sha256": source_sha256,
            "file_size": str(size),
            "extension": path.suffix.lower(),
            "candidate_reason": _reason(
                nyse30=nyse30_hit,
                nyse100=nyse100_hit,
                path_kind=path_kind,
                size=size,
                extension=path.suffix.lower(),
                source_url=source_url,
                rights_tier=rights_tier,
                rights_conflict=rights_conflict,
            ),
            "source_url": source_url,
            "rights_tier": rights_tier or "unknown",
            "eval_allowed": _bool_text(row.get("eval_allowed")),
            "training_allowed": _bool_text(row.get("training_allowed")),
            "commit_allowed": _bool_text(row.get("commit_allowed")),
            "manual_action": "Fill source_url and explicit rights_tier; leave training_allowed=false unless rights explicitly permit.",
            "registration_ready": str(registration_ready).lower(),
        }
        ranked.append((score, output))

    deduped: list[dict[str, str]] = []
    seen_cases: set[str] = set()
    for _, row in sorted(ranked, key=lambda item: item[0]):
        key = row["case_id"] or row["local_path"]
        if key in seen_cases:
            continue
        seen_cases.add(key)
        row["rank"] = str(len(deduped) + 1)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict[str, str]], csv_path: Path) -> None:
    lines = [
        "# Top-30 Manual-Local Registration Actions",
        "",
        "This report ranks transcript candidates for manual rights review. It does not register files, copy raw content, parse transcript bodies, run OCR, edit canonical gold, or train models.",
        "",
        f"- CSV: `{csv_path}`",
        f"- Top rows: `{len(rows)}`",
        "- Registration-ready rows: `0` unless source URL and rights tier are explicitly filled and safe.",
        "- Default rights tier: `unknown`",
        "- Default eval/training/commit flags: `false`",
        "",
        "## Top 30",
        "",
        "| rank | case_id | ticker | fiscal_period | extension | size | registration_ready | action |",
        "|---:|---|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {rank} | `{case_id}` | `{ticker}` | `{period}` | `{extension}` | "
            "{size} | `{ready}` | {action} |".format(
                rank=row["rank"],
                case_id=row["case_id"],
                ticker=row["ticker"],
                period=row["fiscal_period"],
                extension=row["extension"],
                size=row["file_size"],
                ready=row["registration_ready"],
                action=row["manual_action"],
            )
        )
    lines.extend(
        [
            "",
            "## Fields Keith Must Fill",
            "",
            "- `source_url`: original source page or source reference for the transcript.",
            "- `rights_tier`: explicit reviewed tier; do not leave as `unknown` for registration.",
            "- `eval_allowed`: set `true` only when evaluation use is explicitly permitted.",
            "- `training_allowed`: keep `false` unless rights explicitly permit training.",
            "- `commit_allowed`: keep `false`; raw files must not be committed.",
            "- `notes`: concise rights/provenance rationale.",
            "",
            "## Example Safe Completed Row",
            "",
            "```csv",
            "case_id,ticker,company_name,fiscal_period,local_path,source_url,source_type,rights_tier,operator,eval_allowed,training_allowed,commit_allowed,notes",
            "jpm_2026_q1,JPM,JPMorgan Chase & Co.,2026_Q1,/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/JPM_2026_Q1/raw/transcript.txt,https://example.com/company-ir-jpm-q1,manual_local,manual_supplied,Keith,true,false,false,Source URL and rights reviewed; path/hash registration only.",
            "```",
            "",
            "## Registration Command After Review",
            "",
            "Only run registration after removing any rows that remain `registration_ready=false` or completing them with an explicit `source_url`, reviewed safe `rights_tier`, and reviewed permission flags.",
            "",
            "```bash",
            "python scripts/register_manual_local_batch.py --batch data/review/staging/top30_manual_local_registration_actions.csv --dry-run",
            "python scripts/register_manual_local_batch.py --batch data/review/staging/top30_manual_local_registration_actions.csv",
            "python scripts/validate_manual_local_registry.py",
            "python scripts/report_agent1_candidate_generation_readiness.py",
            "```",
            "",
            "Do not copy raw transcript/audio/video files into the repository. Do not set `training_allowed=true` unless the reviewed rights explicitly permit training use. Unknown rights fail closed.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build top-30 manual-local registration action report from metadata only.")
    parser.add_argument("--discovery", default="data/review/staging/manual_local_discovery_candidates.jsonl")
    parser.add_argument("--batch", default="data/review/staging/manual_local_batch_candidate.csv")
    parser.add_argument("--nyse30", default="configs/nyse_30_pilot_targets.yml")
    parser.add_argument("--nyse100", default="data/acquisition/nyse_100_media_manifest.csv")
    parser.add_argument("--csv-out", default="data/review/staging/top30_manual_local_registration_actions.csv")
    parser.add_argument("--report", default="reports/top30_manual_local_registration_actions.md")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args(argv)
    rows = build_top30(
        discovery_path=Path(args.discovery),
        batch_path=Path(args.batch),
        nyse30_path=Path(args.nyse30),
        nyse100_path=Path(args.nyse100),
        limit=args.limit,
    )
    csv_path = Path(args.csv_out)
    write_csv(csv_path, rows)
    write_report(Path(args.report), rows, csv_path)
    print(f"Top-30 manual-local registration action report written: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
