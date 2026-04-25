#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.privacy import redact_pii_text
from signal_engine.signal_baseline import SIGNAL_FAMILY_LABELS, weak_label_signal_family


SCAN_ROOTS = (
    ROOT / "data" / "signal_engine_2_0",
    ROOT / "demo",
    ROOT / "outputs" / "signal_engine_2_0",
)
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt"}
REVIEW_COLUMNS = [
    "id",
    "source_file",
    "domain",
    "text",
    "suggested_label",
    "suggested_evidence_terms",
    "suggestion_confidence",
    "reviewer_label",
    "reviewer_confidence",
    "reviewer_notes",
    "accepted",
]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _iter_text_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                files.append(path)
    return sorted(files)


def _infer_domain(path: Path) -> str:
    lowered = str(path.relative_to(ROOT)).lower()
    if "support" in lowered:
        return "support"
    if "sales" in lowered:
        return "sales"
    if "account" in lowered:
        return "account_management"
    if "earnings" in lowered:
        return "earnings"
    return "unknown"


def _looks_like_content(text: str) -> bool:
    stripped = text.strip()
    if len(stripped.split()) < 5:
        return False
    if stripped.startswith("#"):
        return False
    if stripped.lower().startswith(("http://", "https://", "schema_version", "conversation_id")):
        return False
    if len(stripped) > 500:
        return False
    return any(char.isalpha() for char in stripped)


def _split_text(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks = re.split(r"(?<=[.!?])\s+|(?:\s*[;•]\s*)|(?:\s+-\s+)", normalized)
    fragments: list[str] = []
    for chunk in chunks:
        piece = chunk.strip(" -*")
        if _looks_like_content(piece):
            fragments.append(piece)
        clauses = [part.strip(" ,") for part in re.split(r",\s+(?=(?:if|but|and|so|while|because|without)\b)", piece, flags=re.I)]
        for clause in clauses:
            if clause != piece and _looks_like_content(clause):
                fragments.append(clause)
    return fragments


def _walk_strings(payload: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(payload, str):
        strings.append(payload)
    elif isinstance(payload, list):
        for item in payload:
            strings.extend(_walk_strings(item))
    elif isinstance(payload, dict):
        for value in payload.values():
            strings.extend(_walk_strings(value))
    return strings


def _extract_strings(path: Path) -> list[str]:
    if path.suffix == ".jsonl":
        strings: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            strings.extend(_walk_strings(payload))
        return strings
    if path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return _walk_strings(payload)
    return path.read_text(encoding="utf-8").splitlines()


def _normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _suggestion_confidence(label: str, evidence_terms: list[str], text: str) -> str:
    if label == "neutral":
        return "medium" if len(text.split()) >= 8 else "low"
    if len(evidence_terms) >= 3:
        return "high"
    if len(evidence_terms) >= 1:
        return "medium"
    return "low"


def mine_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for path in _iter_text_files():
        domain = _infer_domain(path)
        for raw in _extract_strings(path):
            for snippet in _split_text(raw):
                redacted = redact_pii_text(snippet)
                text = redacted["text"].strip()
                if not _looks_like_content(text):
                    continue
                key = _normalize_key(text)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                weak = weak_label_signal_family(text, domain=domain)
                candidates.append(
                    {
                        "id": f"candidate_{len(candidates) + 1:04d}",
                        "source_file": _display_path(path),
                        "domain": domain,
                        "text": text,
                        "suggested_label": weak["label"],
                        "suggested_evidence_terms": weak["evidence_terms"],
                        "suggestion_confidence": _suggestion_confidence(weak["label"], list(weak["evidence_terms"]), text),
                        "reviewer_label": "",
                        "reviewer_confidence": "",
                        "reviewer_notes": "",
                        "accepted": "",
                        "pii_redacted": bool(redacted["redactions"]),
                    }
                )
    label_order = {label: index for index, label in enumerate(SIGNAL_FAMILY_LABELS)}
    return sorted(
        candidates,
        key=lambda row: (
            label_order.get(str(row["suggested_label"]), 99),
            -len(list(row["suggested_evidence_terms"])),
            str(row["source_file"]),
            str(row["id"]),
        ),
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _write_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "id": row["id"],
                    "source_file": row["source_file"],
                    "domain": row["domain"],
                    "text": row["text"],
                    "suggested_label": row["suggested_label"],
                    "suggested_evidence_terms": "; ".join(row["suggested_evidence_terms"]),
                    "suggestion_confidence": row["suggestion_confidence"],
                    "reviewer_label": "",
                    "reviewer_confidence": "",
                    "reviewer_notes": "",
                    "accepted": "",
                }
            )


def _render_report(rows: list[dict[str, Any]]) -> str:
    by_label = {label: 0 for label in SIGNAL_FAMILY_LABELS}
    for row in rows:
        by_label[str(row["suggested_label"])] += 1
    lines = [
        "# Signal Label Candidate Mining",
        "",
        "This workflow mines candidate snippets from committed local fixtures, demo assets, and generated outputs.",
        "It is a review-queue builder, not an automatic source of truth.",
        "",
        f"- candidate_count: `{len(rows)}`",
        "",
        "## Suggested Label Mix",
        "",
    ]
    for label in SIGNAL_FAMILY_LABELS:
        lines.append(f"- `{label}`: `{by_label[label]}`")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Local project fixtures remain the primary training source.",
            "- Candidate rows are only suggestions until a reviewer fills `reviewer_label` and marks `accepted`.",
            "- Neutral candidates are intentionally included to avoid a purely issue-heavy queue.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mine reviewable signal label candidates from committed local text artifacts.")
    parser.add_argument(
        "--jsonl-out",
        default=str(ROOT / "data" / "nlp_research" / "signal_label_candidates.jsonl"),
    )
    parser.add_argument(
        "--review-csv-out",
        default=str(ROOT / "data" / "nlp_research" / "signal_label_candidates_review.csv"),
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "signal-label-candidate-mining.md"),
    )
    args = parser.parse_args(argv)

    rows = mine_candidates()
    jsonl_out = Path(args.jsonl_out)
    review_csv_out = Path(args.review_csv_out)
    report_out = Path(args.report_out)

    _write_jsonl(jsonl_out, rows)
    _write_review_csv(review_csv_out, rows)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(_render_report(rows), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "candidate_count": len(rows),
                "jsonl_out": _display_path(jsonl_out),
                "review_csv_out": _display_path(review_csv_out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
