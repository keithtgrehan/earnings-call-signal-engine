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


INPUT_PATH = ROOT / "data" / "nlp_research" / "signal_label_candidates_review.csv"
CSV_OUT = ROOT / "data" / "nlp_research" / "candidate_review_priority_30.csv"
REPORT_OUT = ROOT / "docs" / "candidate-review-priority-30.md"
ALLOWED_LABELS = (
    "risk_friction",
    "opportunity_commitment",
    "uncertainty_hedging",
    "neutral",
)
TARGET_QUOTAS = {
    "neutral": 6,
    "risk_friction": 10,
    "uncertainty_hedging": 4,
    "opportunity_commitment": 10,
}

META_PATTERNS = (
    "signal engine",
    "deterministic",
    "benchmark",
    "canonical",
    "optional ",
    "prompt ",
    "output ",
    "language detected",
    "customer language indicates",
    "low lexical overlap",
    "deflection phrase",
    "matched deterministic",
    "review cautious",
    "realistic synthetic",
    "synthetic pii",
    "prompt did not receive",
    "python scripts/",
    "http://",
    "https://",
    " | ",
    "`",
)
RISK_CUES = (
    "frustrated",
    "expensive",
    "dispute",
    "escalate",
    "unresolved",
    "charged twice",
    "another vendor",
    "downgrade",
    "switch",
    "help center",
    "does not solve",
    "doesn't answer",
    "real date",
    "faq",
    "refund",
    "failed resolution",
    "ticket ",
    "leadership is asking",
    "reduce seats",
    "seat reduction",
    "will not move",
    "without a concrete next step",
)
UNCERTAINTY_CUES = (
    "for now",
    "if ",
    "may ",
    "might ",
    "probably",
    "not sure",
    "unclear",
    "still reviewing",
    "wait for",
    "confused",
    "don't understand",
    "concerned",
)
NEUTRAL_CUES = (
    "next week",
    "next tuesday",
    "this afternoon",
    "by friday",
    "how teams usually evaluate",
    "pilot scope",
    "rollout plan",
    "security packet",
    "proposal by tuesday",
)
OPPORTUNITY_CUES = (
    "i own",
    "will send",
    "proposal by tuesday",
    "security packet",
    "recovery plan",
    "named owners",
    "confirm owners",
    "happy",
    "solved it",
)
PLACEHOLDER_TOKENS = ("[PHONE]", "[EMAIL]", "[CARD]", "[ADDRESS]", "[IBAN]")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _source_priority(source_file: str) -> int:
    if source_file.startswith("data/signal_engine_2_0/"):
        return 3
    if source_file.startswith("demo/signal_engine_2_0/"):
        return 2
    if source_file.startswith("outputs/signal_engine_2_0/"):
        return 1
    return 0


def _text_quality_score(text: str) -> tuple[int, str]:
    words = len(text.split())
    if 6 <= words <= 20:
        return 14, "short readable snippet"
    if 4 <= words <= 24:
        return 8, "compact snippet"
    if words <= 32:
        return 3, "slightly longer but still reviewable"
    return -6, "longer snippet"


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def _likely_meta(text: str, source_file: str) -> bool:
    lowered = text.lower()
    if "dataset_manifests/" in source_file:
        return True
    if any(pattern in lowered for pattern in META_PATTERNS):
        return True
    if text.startswith("/") or text.startswith("`/"):
        return True
    return False


def _obvious_pii_or_placeholder(text: str) -> bool:
    redacted = redact_pii_text(text)
    if redacted["redactions"]:
        return True
    return any(token in text for token in PLACEHOLDER_TOKENS)


def _plausible_for_label(label: str, text: str, terms: list[str], source_file: str) -> bool:
    lowered = text.lower()
    if _likely_meta(text, source_file):
        return False
    if label == "neutral":
        if not source_file.startswith("data/signal_engine_2_0/"):
            return False
        if _obvious_pii_or_placeholder(text):
            return False
        if terms:
            return False
        if _contains_any(lowered, RISK_CUES) or _contains_any(lowered, UNCERTAINTY_CUES) or _contains_any(lowered, OPPORTUNITY_CUES):
            return False
        if len(lowered.split()) < 5:
            return False
        if "..." in text:
            return False
        return True
    if label == "risk_friction":
        return _contains_any(lowered, RISK_CUES) or len(terms) >= 2
    if label == "uncertainty_hedging":
        return _contains_any(lowered, UNCERTAINTY_CUES) or "for now" in lowered
    if label == "opportunity_commitment":
        if _contains_any(lowered, RISK_CUES):
            return False
        return _contains_any(lowered, OPPORTUNITY_CUES) or ("send" in lowered and len(terms) >= 1)
    return True


def _evidence_terms(row: dict[str, str]) -> list[str]:
    return [term.strip() for term in str(row.get("suggested_evidence_terms", "")).split(";") if term.strip()]


def _label_priority(label: str) -> tuple[int, str]:
    mapping = {
        "neutral": (40, "neutral coverage"),
        "risk_friction": (38, "clear friction coverage"),
        "uncertainty_hedging": (36, "uncertainty coverage"),
        "opportunity_commitment": (24, "commitment coverage"),
    }
    return mapping.get(label, (0, "fallback coverage"))


def _clarity_bonus(label: str, text: str, terms: list[str]) -> tuple[int, str]:
    lowered = text.lower()
    if label == "risk_friction" and (_contains_any(lowered, RISK_CUES) or len(terms) >= 2):
        return 14, "explicit friction cue"
    if label == "uncertainty_hedging" and (_contains_any(lowered, UNCERTAINTY_CUES) or len(terms) >= 1):
        return 14, "explicit hedge cue"
    if label == "neutral" and (_contains_any(lowered, NEUTRAL_CUES) or len(terms) == 0):
        return 12, "logistics or status wording"
    if label == "opportunity_commitment" and ("i own" in lowered or "will send" in lowered or "proposal" in lowered):
        return 10, "concrete commitment wording"
    return 0, "limited cue strength"


def _score_row(row: dict[str, str]) -> dict[str, Any]:
    text = row["text"].strip()
    label = row["suggested_label"].strip()
    terms = _evidence_terms(row)
    reasons: list[str] = []
    score = 0

    label_points, label_reason = _label_priority(label)
    score += label_points
    reasons.append(label_reason)

    source_points = {3: 18, 2: 8, 1: 2, 0: 0}[_source_priority(row["source_file"])]
    score += source_points
    if source_points:
        reasons.append("local transcript-side source")

    if row["domain"] != "unknown":
        score += 8
        reasons.append("known business domain")
    else:
        score -= 4

    length_points, length_reason = _text_quality_score(text)
    score += length_points
    reasons.append(length_reason)

    evidence_points = min(len(terms), 4) * 3
    score += evidence_points
    if terms:
        reasons.append("strong evidence terms")

    clarity_points, clarity_reason = _clarity_bonus(label, text, terms)
    score += clarity_points
    if clarity_points > 0:
        reasons.append(clarity_reason)

    plausible = _plausible_for_label(label, text, terms, row["source_file"])
    if plausible:
        score += 12
        reasons.append("label-text match looks plausible")
    else:
        score -= 25
        reasons.append("label-text match is weak")

    if _likely_meta(text, row["source_file"]):
        score -= 45
        reasons.append("meta or report text")

    if _obvious_pii_or_placeholder(text):
        score -= 18
        reasons.append("contains placeholder or pii marker")

    if "..." in text:
        score -= 10
        reasons.append("truncated snippet")

    if len(reasons) == 0:
        reasons.append("manual review candidate")

    return {
        **row,
        "plausible": plausible,
        "priority_score": score,
        "priority_reason": "; ".join(dict.fromkeys(reasons)),
    }


def prioritize_rows(rows: list[dict[str, str]], limit: int = 30) -> list[dict[str, str]]:
    scored = [_score_row(row) for row in rows if not str(row.get("accepted", "")).strip()]
    by_label: dict[str, list[dict[str, Any]]] = {label: [] for label in ALLOWED_LABELS}
    for row in scored:
        if row["suggested_label"] in by_label:
            by_label[row["suggested_label"]].append(row)
    for label in by_label:
        by_label[label].sort(
            key=lambda row: (
                -int(row["priority_score"]),
                row["domain"] == "unknown",
                len(row["text"].split()),
                row["id"],
            )
        )

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for label, quota in TARGET_QUOTAS.items():
        for row in by_label[label]:
            if len([item for item in selected if item["suggested_label"] == label]) >= quota:
                break
            if row["id"] in selected_ids:
                continue
            if not bool(row["plausible"]):
                continue
            if int(row["priority_score"]) < 35:
                continue
            selected.append(row)
            selected_ids.add(row["id"])

    remaining = sorted(
        [row for row in scored if row["id"] not in selected_ids],
        key=lambda row: (
            not bool(row["plausible"]),
            -int(row["priority_score"]),
            row["suggested_label"] not in {"neutral", "risk_friction", "uncertainty_hedging"},
            row["domain"] == "unknown",
            len(row["text"].split()),
            row["id"],
        ),
    )
    for row in remaining:
        if len(selected) >= limit:
            break
        selected.append(row)
        selected_ids.add(row["id"])

    final_rows = sorted(
        selected[:limit],
        key=lambda row: (
            {"neutral": 0, "risk_friction": 1, "uncertainty_hedging": 2, "opportunity_commitment": 3}.get(
                row["suggested_label"], 9
            ),
            -int(row["priority_score"]),
            row["id"],
        ),
    )
    return [
        {
            "id": row["id"],
            "source_file": row["source_file"],
            "domain": row["domain"],
            "text": row["text"],
            "suggested_label": row["suggested_label"],
            "suggested_evidence_terms": row["suggested_evidence_terms"],
            "priority_reason": row["priority_reason"],
            "reviewer_label": "",
            "reviewer_confidence": "",
            "reviewer_notes": "",
            "accepted": "",
        }
        for row in final_rows
    ]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "id",
        "source_file",
        "domain",
        "text",
        "suggested_label",
        "suggested_evidence_terms",
        "priority_reason",
        "reviewer_label",
        "reviewer_confidence",
        "reviewer_notes",
        "accepted",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_report(rows: list[dict[str, str]]) -> str:
    counts = {label: 0 for label in ALLOWED_LABELS}
    for row in rows:
        counts[row["suggested_label"]] += 1
    lines = [
        "# Candidate Review Priority 30",
        "",
        "This packet selects the highest-value mined candidate rows for a fast human review pass.",
        "",
        "Selection priorities:",
        "",
        "- neutral coverage",
        "- clear risk_friction turns",
        "- the small number of clean uncertainty_hedging examples",
        "- short readable snippets",
        "- strong evidence terms",
        "- no obvious PII or placeholder-heavy rows",
        "",
        "## Packet Mix",
        "",
    ]
    for label in ALLOWED_LABELS:
        lines.append(f"- `{label}`: `{counts[label]}`")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is a review queue, not an auto-promotion list.",
            "- Candidate rows still require manual reviewer labels and explicit acceptance.",
            "- Loughran-McDonald terms, when available, are evidence aids only.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prioritize the best 30 mined candidate rows for human review.")
    parser.add_argument("--input-path", default=str(INPUT_PATH))
    parser.add_argument("--csv-out", default=str(CSV_OUT))
    parser.add_argument("--report-out", default=str(REPORT_OUT))
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args(argv)

    rows = _read_rows(Path(args.input_path))
    prioritized = prioritize_rows(rows, limit=args.limit)
    _write_csv(Path(args.csv_out), prioritized)
    Path(args.report_out).write_text(_render_report(prioritized), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "priority_count": len(prioritized),
                "csv_out": str(Path(args.csv_out)),
                "report_out": str(Path(args.report_out)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
