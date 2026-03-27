from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SOURCE_TYPE_LABELS = {
    "transcript": "Transcript",
    "results_release": "Results release",
    "presentation": "Deck",
    "follow_up_transcript": "Follow-up transcript",
    "shareholder_letter": "Shareholder letter",
    "financials": "Financials",
}


def load_demo_case_catalog(repo_root: Path) -> list[dict[str, str]]:
    demo_root = repo_root / "data" / "demo_cases"
    cases: list[dict[str, str]] = []
    if not demo_root.exists():
        return cases

    for case_root in sorted(path for path in demo_root.iterdir() if path.is_dir()):
        fixture_path = case_root / "demo" / "fixtures" / f"{case_root.name}_fixture.json"
        if not fixture_path.exists():
            continue
        fixture = _load_json(fixture_path)
        if not isinstance(fixture, dict):
            continue
        cases.append(
            {
                "case_id": str(fixture.get("case_id", case_root.name)),
                "company": str(fixture.get("company", case_root.name.replace("_", " ").title())),
                "quarter": str(fixture.get("quarter", "")),
                "label": f"{fixture.get('company', case_root.name)} {fixture.get('quarter', '')}".strip(),
            }
        )
    return cases


def load_demo_case_payload(repo_root: Path, case_id: str) -> dict[str, Any] | None:
    case_root = repo_root / "data" / "demo_cases" / case_id
    fixture_path = case_root / "demo" / "fixtures" / f"{case_id}_fixture.json"
    if not fixture_path.exists():
        return None

    fixture = _load_json(fixture_path)
    artifact_paths = fixture.get("artifact_paths", {})
    evidence_rows = _load_rows(case_root, artifact_paths.get("evidence_rows"))
    joined_audio_rows = _load_rows(case_root, artifact_paths.get("joined_qa_audio_review"), optional=True)
    market_context = _load_json(case_root / artifact_paths["market_context"])
    summary = _load_json(case_root / artifact_paths["summary"])

    preview_row_ids = set(fixture.get("preview_row_ids", []))
    enriched_rows = [_enrich_evidence_row(row, preview_row_ids=preview_row_ids) for row in evidence_rows]
    enriched_joined_rows = [_enrich_joined_row(row) for row in joined_audio_rows]
    top_concerns = [row["plain_english_label"] for row in enriched_rows[:3]]
    artifact_links = [
        {
            "label": _humanize_artifact_key(key),
            "relative_path": rel_path,
            "url_path": rel_path.replace("\\", "/"),
        }
        for key, rel_path in artifact_paths.items()
        if rel_path and (case_root / rel_path).exists()
    ]

    pressure_rows = [
        row
        for row in enriched_rows
        if "analyst-pressure" in row["categories"] or "hedging-caution" in row["categories"]
    ]

    return {
        "case_id": case_id,
        "company": str(fixture.get("company", case_id)),
        "quarter": str(fixture.get("quarter", "")),
        "display_name": str(summary.get("display_name", fixture.get("company", case_id))),
        "case_status": str(fixture.get("case_status", "ready")),
        "verdict": _pick_verdict(summary, enriched_rows),
        "top_concerns": top_concerns,
        "trust_statement": "Evidence-backed review aid, not a trading system.",
        "headline_counts": summary.get("headline_counts", {}),
        "summary_points": list(summary.get("top_summary_points", [])),
        "limitations": list(summary.get("limitations", [])),
        "evidence_rows": enriched_rows,
        "joined_audio_rows": enriched_joined_rows,
        "audio_support_available": bool(enriched_joined_rows),
        "pressure_rows": pressure_rows[:4],
        "market_context": market_context,
        "fixture": fixture,
        "summary": summary,
        "artifact_links": artifact_links,
        "source_filters": _build_source_filters(enriched_rows),
    }


def _load_rows(case_root: Path, relative_path: str | None, *, optional: bool = False) -> list[dict[str, Any]]:
    if not relative_path:
        return []
    path = case_root / relative_path
    if optional and not path.exists():
        return []
    payload = _load_json(path)
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_verdict(summary: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> str:
    for point in summary.get("top_summary_points", []):
        lowered = point.lower()
        if "quarter-consistent" in lowered or "source of truth" in lowered or "supporting context only" in lowered:
            continue
        return str(point)
    labels = [row["plain_english_label"] for row in evidence_rows[:3]]
    if not labels:
        return "Transcript-first review package ready."
    return "; ".join(labels[:3]).capitalize() + "."


def _enrich_evidence_row(row: dict[str, Any], *, preview_row_ids: set[str]) -> dict[str, Any]:
    source_type = str(row.get("source_type", "")).strip()
    categories = _classify_categories(row)
    enriched = dict(row)
    enriched["source_type_label"] = SOURCE_TYPE_LABELS.get(source_type, source_type.replace("_", " ").title())
    enriched["categories"] = categories
    enriched["source_type_slug"] = source_type.replace("_", "-")
    enriched["priority_class"] = str(row.get("review_priority", "medium")).lower()
    enriched["is_top_moment"] = row.get("row_id") in preview_row_ids or int(row.get("display_order", 99)) <= 5
    return enriched


def _classify_categories(row: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    text = " ".join(
        str(row.get(key, ""))
        for key in [
            "plain_english_label",
            "extracted_signal",
            "why_it_matters",
            "ambiguity_note",
            "source_section_or_speaker",
        ]
    ).lower()
    source_type = str(row.get("source_type", "")).lower()

    if any(token in text for token in ["guidance", "outlook", "guide", "expense", "capex", "budget", "margin", "net adds"]):
        categories.append("guidance-outlook")
    if any(token in text for token in ["hedg", "qualified", "cautious", "caution", "pressure", "headwind", "slowdown", "macro"]):
        categories.append("hedging-caution")
    if source_type == "follow_up_transcript" or "q&a" in text or any(token in text for token in ["analyst", "pushback", "follow-up"]):
        categories.append("analyst-pressure")
    if source_type in {"results_release", "presentation", "financials"}:
        categories.append("financial-context")
    if row.get("has_audio_support"):
        categories.append("audio-supported")
    if not categories:
        categories.append("all")
    return categories


def _enrich_joined_row(row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    enriched["hedge_marker_count"] = len(row.get("transcript_hedge_markers", []))
    return enriched


def _humanize_artifact_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _build_source_filters(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    filters: list[dict[str, str]] = []
    for row in rows:
        source_type = row["source_type"]
        if source_type in seen:
            continue
        seen.add(source_type)
        filters.append(
            {
                "value": row["source_type_slug"],
                "label": row["source_type_label"],
            }
        )
    return filters
