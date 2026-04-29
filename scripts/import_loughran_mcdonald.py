#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.lexicons import DEFAULT_LEXICON_PATH, LM_CATEGORY_NAMES


SOURCE_GLOB = "Loughran-McDonald_MasterDictionary_*.csv"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _find_source_file(input_dir: Path) -> Path | None:
    matches = sorted(input_dir.glob(SOURCE_GLOB))
    return matches[0] if matches else None


def _word_column(fieldnames: list[str]) -> str | None:
    for candidate in ("Word", "word", "Token", "token", "Term", "term"):
        if candidate in fieldnames:
            return candidate
    return None


def _flag_value(row: dict[str, str], *candidates: str) -> bool:
    for candidate in candidates:
        if candidate not in row:
            continue
        raw = str(row.get(candidate, "")).strip()
        if not raw:
            return False
        try:
            return float(raw) > 0
        except ValueError:
            return raw.lower() in {"true", "yes", "y", "1"}
    return False


def _normalize_term(raw: str) -> str:
    return " ".join(str(raw).strip().lower().replace("_", " ").split())


def import_loughran_mcdonald(source_path: Path) -> dict[str, Any]:
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing header row in {source_path}")
        word_column = _word_column(reader.fieldnames)
        if not word_column:
            raise ValueError(f"Could not identify word column in {source_path}")

        buckets = {category: set() for category in LM_CATEGORY_NAMES}
        for row in reader:
            term = _normalize_term(row.get(word_column, ""))
            if not term or len(term) < 2:
                continue
            if _flag_value(row, "Negative", "negative"):
                buckets["negative"].add(term)
            if _flag_value(row, "Positive", "positive"):
                buckets["positive"].add(term)
            if _flag_value(row, "Uncertainty", "uncertainty"):
                buckets["uncertainty"].add(term)
            if _flag_value(row, "Litigious", "litigious"):
                buckets["litigious"].add(term)
            if _flag_value(row, "Constraining", "constraining"):
                buckets["constraining"].add(term)
            if _flag_value(
                row,
                "Weak_Modal",
                "Strong_Modal",
                "Weak Modal",
                "Strong Modal",
                "weak_modal",
                "strong_modal",
            ):
                buckets["modal"].add(term)

    return {
        **{category: sorted(buckets[category]) for category in LM_CATEGORY_NAMES},
        "_metadata": {
            "source_file": _display_path(source_path),
            "imported_at_utc": datetime.now(UTC).isoformat(),
            "category_counts": {category: len(buckets[category]) for category in LM_CATEGORY_NAMES},
            "license_review_note": (
                "Review the official Loughran-McDonald distribution terms before committing the normalized artifact."
            ),
        },
    }


def _render_report(status: dict[str, Any]) -> str:
    lines = [
        "# Loughran-McDonald Integration",
        "",
        "This repo treats Loughran-McDonald as canonical lexical support when a local, license-reviewed dictionary export is available.",
        "The raw external CSV is never required for CI, and the baseline still works without it.",
        "",
        f"- status: `{status['status']}`",
        f"- expected_input_dir: `{status['expected_input_dir']}`",
        f"- canonical_usage: `optional deterministic lexical support`",
        "",
    ]
    if status["status"] == "ok":
        lines.extend(
            [
                f"- source_file: `{status['source_file']}`",
                f"- normalized_artifact: `{status['normalized_artifact']}`",
                "",
                "## Imported Categories",
                "",
            ]
        )
        for category, count in status["category_counts"].items():
            lines.append(f"- `{category}`: `{count}` terms")
        lines.extend(
            [
                "",
                "## Integration Notes",
                "",
                "- The normalized artifact is intentionally lightweight and auditable.",
                "- Local project fixtures remain the primary training corpus.",
                "- Review license posture before checking the normalized artifact into version control.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Blocked Status",
                "",
                "- No local Loughran-McDonald CSV was found under the expected external data path.",
                "- This is not a runtime failure for the repo. Deterministic rules continue to work without the finance dictionary.",
                "",
                "## Manual Steps",
                "",
                "1. Place an official Loughran-McDonald master dictionary CSV in `data/external/loughran_mcdonald/`.",
                "2. Run `python scripts/import_loughran_mcdonald.py`.",
                "3. Review the generated normalized artifact before committing it.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a local Loughran-McDonald master dictionary CSV.")
    parser.add_argument(
        "--input-dir",
        default=str(ROOT / "data" / "external" / "loughran_mcdonald"),
    )
    parser.add_argument(
        "--json-out",
        default=str(DEFAULT_LEXICON_PATH),
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "loughran-mcdonald-integration.md"),
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    json_out = Path(args.json_out)
    report_out = Path(args.report_out)

    source_file = _find_source_file(input_dir)
    if source_file is None:
        status = {
            "status": "blocked_missing_source",
            "expected_input_dir": _display_path(input_dir),
            "normalized_artifact": _display_path(json_out),
        }
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(_render_report(status), encoding="utf-8")
        print(json.dumps(status, indent=2))
        return 0

    payload = import_loughran_mcdonald(source_file)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    status = {
        "status": "ok",
        "expected_input_dir": _display_path(input_dir),
        "source_file": _display_path(source_file),
        "normalized_artifact": _display_path(json_out),
        "category_counts": payload["_metadata"]["category_counts"],
    }
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(_render_report(status), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
