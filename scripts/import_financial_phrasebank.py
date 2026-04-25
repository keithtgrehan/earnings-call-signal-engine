#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_LABELS = {"positive", "negative", "neutral"}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _candidate_files(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for pattern in ("*.csv", "*.tsv", "*.txt")
        for path in input_dir.glob(pattern)
        if path.is_file()
    )


def _normalize_label(raw: str) -> str | None:
    value = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    if value in ALLOWED_LABELS:
        return value
    return None


def _parse_delimited_file(path: Path, delimiter: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            return []
        text_key = next((name for name in reader.fieldnames if name.lower() in {"text", "sentence", "phrase"}), None)
        label_key = next((name for name in reader.fieldnames if name.lower() in {"label", "sentiment"}), None)
        if not text_key or not label_key:
            return []
        rows: list[dict[str, str]] = []
        for row in reader:
            text = str(row.get(text_key, "")).strip()
            label = _normalize_label(row.get(label_key, ""))
            if text and label:
                rows.append({"text": text, "label": label})
        return rows


def _parse_text_file(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "@" in stripped:
            raw_label, text = stripped.split("@", 1)
        elif "\t" in stripped:
            raw_label, text = stripped.split("\t", 1)
        else:
            continue
        label = _normalize_label(raw_label)
        if label and text.strip():
            rows.append({"text": text.strip(), "label": label})
    return rows


def import_phrasebank_rows(input_dir: Path) -> tuple[list[dict[str, str]], list[str]]:
    normalized: list[dict[str, str]] = []
    sources: list[str] = []
    for path in _candidate_files(input_dir):
        parsed: list[dict[str, str]] = []
        if path.suffix == ".csv":
            parsed = _parse_delimited_file(path, ",")
        elif path.suffix == ".tsv":
            parsed = _parse_delimited_file(path, "\t")
        else:
            parsed = _parse_text_file(path)
        if parsed:
            normalized.extend(parsed)
            sources.append(_display_path(path))
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        key = (row["label"], " ".join(row["text"].split()).lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped, sources


def _render_report(status: dict[str, object]) -> str:
    lines = [
        "# Financial PhraseBank Benchmark Adapter",
        "",
        "Financial PhraseBank is treated as a benchmark-only sanity-check resource in this repo.",
        "It is not canonical training data and is never mixed into the local support/sales/account-management corpus automatically.",
        "",
        f"- status: `{status['status']}`",
        f"- expected_input_dir: `{status['expected_input_dir']}`",
        f"- default_path: `benchmark_only`",
        "",
    ]
    if status["status"] == "ok":
        lines.extend(
            [
                f"- normalized_rows: `{status['row_count']}`",
                f"- normalized_out: `{status['normalized_out']}`",
                "",
                "## Imported Sources",
                "",
            ]
        )
        for source in status["sources"]:
            lines.append(f"- `{source}`")
        lines.extend(
            [
                "",
                "## What This Is For",
                "",
                "- benchmark-only finance sentiment sanity checks",
                "- quick regression comparisons against the canonical local corpus",
                "- documentation of external finance benchmark readiness",
                "",
                "## What Not To Do",
                "",
                "- do not merge PhraseBank rows into the canonical training set",
                "- do not treat PhraseBank performance as proof of transcript review quality",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Blocked Status",
                "",
                "- No local PhraseBank files were found under `data/external/financial_phrasebank/`.",
                "- CI and benchmark scripts should continue without it.",
                "",
                "## Manual Steps",
                "",
                "1. Place a locally licensed PhraseBank export in `data/external/financial_phrasebank/`.",
                "2. Run `python scripts/import_financial_phrasebank.py`.",
                "3. Use the normalized output only for benchmark-only sanity checks.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a local Financial PhraseBank export into a normalized benchmark-only JSONL.")
    parser.add_argument("--input-dir", default=str(ROOT / "data" / "external" / "financial_phrasebank"))
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "benchmark_external" / "financial_phrasebank_normalized.jsonl"),
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "financial-phrasebank-benchmark.md"),
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    out_path = Path(args.out)
    report_path = Path(args.report_out)
    rows, sources = import_phrasebank_rows(input_dir)

    if not rows:
        status = {
            "status": "blocked_missing_source",
            "expected_input_dir": _display_path(input_dir),
            "normalized_out": _display_path(out_path),
            "sources": [],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_render_report(status), encoding="utf-8")
        print(json.dumps(status, indent=2))
        return 0

    normalized_rows = [
        {
            "id": f"phrasebank_{index:04d}",
            "text": row["text"],
            "label": row["label"],
            "source": "; ".join(sources),
            "license_note": "Benchmark-only import from local PhraseBank export; verify dataset terms before reuse.",
            "benchmark_only": True,
            "imported_at_utc": datetime.now(UTC).isoformat(),
        }
        for index, row in enumerate(rows, start=1)
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in normalized_rows) + "\n",
        encoding="utf-8",
    )
    status = {
        "status": "ok",
        "expected_input_dir": _display_path(input_dir),
        "normalized_out": _display_path(out_path),
        "row_count": len(normalized_rows),
        "sources": sources,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
