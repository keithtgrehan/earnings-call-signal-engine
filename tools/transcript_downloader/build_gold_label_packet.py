#!/usr/bin/env python3
"""Build lightweight human-review packets for scaffolded gold labels.

This script never writes gold_labels.jsonl and never promotes weak labels.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_common import enforce_exact_root, enforce_repo_safety  # noqa: E402

ALLOWED_LABELS = {"risk_friction", "opportunity_commitment", "uncertainty_hedging", "neutral"}
LABEL_MAP = {
    "risk_friction": "risk_friction",
    "analyst_pressure": "risk_friction",
    "opportunity_commitment": "opportunity_commitment",
    "commitment": "opportunity_commitment",
    "uncertainty": "uncertainty_hedging",
    "uncertainty_hedging": "uncertainty_hedging",
    "guidance_revision": "opportunity_commitment",
    "neutral": "neutral",
}
PATTERN_CANDIDATES: tuple[tuple[str, str, str], ...] = (
    ("uncertainty_hedging", "medium", r"\b(?:uncertain|uncertainty|difficult to predict|limited visibility|subject to|depends on|could|may|might)\b"),
    ("risk_friction", "medium", r"\b(?:pressure|headwind|weakness|constraint|risk|decline|challenging|slowdown)\b"),
    ("opportunity_commitment", "medium", r"\b(?:confident|committed|we expect|we will|on track|strong demand|well positioned)\b"),
    ("neutral", "low", r"\b(?:revenue|gross margin|operating expenses|capital expenditures|cash flow)\b"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--target-per-case", type=int, default=None, help="Preferred candidate count per case.")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def normalize_quote(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentence_bounds(text: str, pos: int) -> tuple[int, int]:
    start = max(text.rfind(".", 0, pos), text.rfind("\n", 0, pos), text.rfind("?", 0, pos), text.rfind("!", 0, pos))
    start = 0 if start < 0 else start + 1
    end_candidates = [idx for idx in (text.find(".", pos), text.find("\n", pos), text.find("?", pos), text.find("!", pos)) if idx >= 0]
    end = min(end_candidates) + 1 if end_candidates else min(len(text), pos + 320)
    return start, end


def is_low_quality_quote(quote: str) -> bool:
    lowered = quote.lower()
    if re.search(r"\b(operator|you may disconnect|replay|forward-looking|actual results may differ)\b", lowered):
        return True
    if len(quote.split()) < 8:
        return True
    return False


def candidates_from_weak_labels(case_id: str, rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for row in rows:
        quote = normalize_quote(str(row.get("text_span") or row.get("evidence_text") or ""))
        if len(quote) < 40 or is_low_quality_quote(quote):
            continue
        raw_label = str(row.get("type") or row.get("signal_type") or "neutral")
        label = LABEL_MAP.get(raw_label, "neutral")
        candidates.append(
            {
                "exact_quote": quote,
                "suggested_label": label,
                "suggested_confidence": "medium" if float(row.get("confidence") or 0) >= 0.55 else "low",
                "reason": f"Candidate came from deterministic weak-label rule `{raw_label}`; human review required.",
                "source_file": f"{case_id}/labels/weak_labels.jsonl",
            }
        )
    return candidates


def candidates_from_raw(case_id: str, raw_text: str, needed: int) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    used_spans: set[tuple[int, int]] = set()
    for label, confidence, pattern in PATTERN_CANDIDATES:
        for match in re.finditer(pattern, raw_text, flags=re.IGNORECASE):
            start, end = sentence_bounds(raw_text, match.start())
            if (start, end) in used_spans:
                continue
            quote = normalize_quote(raw_text[start:end])
            if len(quote) < 50 or len(quote) > 600 or is_low_quality_quote(quote):
                continue
            used_spans.add((start, end))
            candidates.append(
                {
                    "exact_quote": quote,
                    "suggested_label": label,
                    "suggested_confidence": confidence,
                    "reason": f"Keyword match for `{match.group(0)}` surfaced this exact transcript sentence; human review required.",
                    "source_file": f"{case_id}/raw/transcript.txt",
                }
            )
            if len(candidates) >= needed:
                return candidates
    return candidates


def dedupe(candidates: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        quote = candidate["exact_quote"]
        key = quote.lower()
        if key in seen or candidate["suggested_label"] not in ALLOWED_LABELS:
            continue
        seen.add(key)
        result.append(candidate)
        if len(result) >= limit:
            break
    return result


def render_packet(case_id: str, candidates: list[dict[str, str]]) -> str:
    lines = [
        f"# Human Labeling Packet: {case_id}",
        "",
        "These are machine-surfaced candidates only. Do not treat them as gold labels until Keith confirms or edits them.",
        "",
    ]
    for index, candidate in enumerate(candidates, start=1):
        lines.extend(
            [
                f"## CAND-{index:02d}",
                "",
                f"- candidate_id: `{case_id}_CAND_{index:02d}`",
                f"- suggested_label: `{candidate['suggested_label']}`",
                f"- suggested_confidence: `{candidate['suggested_confidence']}`",
                f"- reason: {candidate['reason']}",
                f"- source_file: `{candidate['source_file']}`",
                '- note: "Suggestion only — human must confirm or edit."',
                "",
                "```text",
                candidate["exact_quote"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_tracker(case_ids: list[str], root: Path) -> str:
    lines = [
        "# Gold Labeling Review Packet",
        "",
        "Use these packet files to choose human-reviewed gold labels. Weak labels are suggestions only.",
        "",
        "| case_id | packet | selected 5 labels | confirmed exact quotes | confirmed final labels | saved JSONL | validated |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case_id in case_ids:
        packet = root / case_id / "labels" / "human_labeling_packet.md"
        lines.append(f"| {case_id} | `{packet}` | [ ] | [ ] | [ ] | [ ] | [ ] |")
    lines.extend(
        [
            "",
            "After editing `gold_labels.jsonl`, run:",
            "",
            "```bash",
            'python tools/transcript_downloader/validate_gold_labels.py --root "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"',
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    enforce_repo_safety()
    root = enforce_exact_root(Path(args.root))
    limit = int(args.target_per_case or args.limit)
    case_dirs = sorted([path for path in root.iterdir() if path.is_dir() and (path / "raw" / "transcript.txt").exists()])
    case_ids: list[str] = []
    for case_dir in case_dirs:
        case_id = case_dir.name
        case_ids.append(case_id)
        weak_rows = load_jsonl(case_dir / "labels" / "weak_labels.jsonl")
        raw_text = (case_dir / "raw" / "transcript.txt").read_text(encoding="utf-8", errors="replace")
        candidates = candidates_from_weak_labels(case_id, weak_rows)
        candidates.extend(candidates_from_raw(case_id, raw_text, max(0, limit - len(candidates))))
        selected = dedupe(candidates, limit)
        packet_path = case_dir / "labels" / "human_labeling_packet.md"
        packet_path.write_text(render_packet(case_id, selected), encoding="utf-8")
        print(f"Wrote {packet_path} ({len(selected)} candidate(s))")
    tracker = repo_root = Path(__file__).resolve().parents[2]
    (tracker / "docs" / "gold-labeling-review-packet.md").write_text(render_tracker(case_ids, root), encoding="utf-8")
    print(f"Wrote {tracker / 'docs' / 'gold-labeling-review-packet.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
