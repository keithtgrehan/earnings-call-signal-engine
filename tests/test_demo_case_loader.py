import json
from pathlib import Path

from earnings_call_sentiment.demo_case_loader import load_demo_case_catalog, load_demo_case_payload


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_demo_case_catalog_lists_fixed_capstone_cases() -> None:
    catalog = load_demo_case_catalog(REPO_ROOT)
    case_ids = {row["case_id"] for row in catalog}

    assert "netflix_q1_2022" in case_ids
    assert "meta_q3_2022" in case_ids
    assert "nvidia_q4_fy2024" in case_ids


def test_demo_case_payload_uses_shared_contract() -> None:
    payload = load_demo_case_payload(REPO_ROOT, "meta_q3_2022")

    assert payload is not None
    assert payload["case_id"] == "meta_q3_2022"
    assert payload["display_name"] == "Meta Q3 2022"
    assert payload["top_concerns"]
    assert payload["trust_statement"] == "Evidence-backed review aid, not a trading system."
    assert payload["evidence_rows"][0].keys() >= {
        "row_id",
        "case_id",
        "source_type",
        "source_excerpt",
        "source_section_or_speaker",
        "extracted_signal",
        "plain_english_label",
        "why_it_matters",
        "ambiguity_note",
        "review_priority",
        "has_audio_support",
        "audio_row_id",
        "audio_summary",
        "optional_timestamp",
        "display_order",
        "source_type_label",
        "categories",
        "source_type_slug",
        "priority_class",
        "is_top_moment",
    }
    assert payload["joined_audio_rows"][0].keys() >= {
        "row_id",
        "case_id",
        "plain_english_label",
        "analyst_question_excerpt",
        "management_answer_excerpt",
        "plain_english_interpretation",
        "plain_english_audio_summary",
        "transcript_hedge_markers",
        "question_time_range",
        "answer_time_range",
        "review_priority",
        "hedge_marker_count",
    }
    assert payload["market_context"]["source"].keys() == {"primary_url", "secondary_url"}
    assert payload["fixture"]["preview_row_ids"]


def test_demo_case_payload_tolerates_missing_optional_audio_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path
    case_id = "demo_case"
    case_root = repo_root / "data" / "demo_cases" / case_id
    (case_root / "demo" / "fixtures").mkdir(parents=True)
    (case_root / "demo" / "summary").mkdir(parents=True)
    (case_root / "demo" / "evidence_rows").mkdir(parents=True)

    fixture = {
        "case_id": case_id,
        "company": "Demo Co",
        "quarter": "Q1 2026",
        "case_status": "ready",
        "preview_row_ids": ["row_1"],
        "notes": ["Demo case for optional artifact fallback testing."],
        "artifact_paths": {
            "summary": "demo/summary/demo_case_summary.json",
            "market_context": "demo/summary/demo_case_market_context.json",
            "evidence_rows": "demo/evidence_rows/demo_case_evidence_rows.json",
            "joined_qa_audio_review": "processed/joined_review/joined_qa_audio_review.json",
        },
    }
    summary = {
        "display_name": "Demo Co Q1 2026",
        "headline_counts": {"audio_review_moments": 0},
        "top_summary_points": ["Transcript-first package ready."],
        "limitations": ["Audio review moments were not packaged for this case."],
    }
    market_context = {
        "panel_title": "Market context",
        "key_extracted_signals": ["Revenue pressure remained visible in prepared remarks."],
        "market_reaction_window": {
            "start_date": "2026-01-01",
            "end_date": "2026-01-02",
            "reaction_magnitude_pct": -1.2,
        },
        "market_reaction_note": "Context only.",
        "source": {"primary_url": "", "secondary_url": ""},
        "caveat": "Contextual sanity-check evidence only.",
    }
    evidence_rows = {
        "rows": [
            {
                "row_id": "row_1",
                "case_id": case_id,
                "source_type": "transcript",
                "source_excerpt": "We remain cautious on near-term demand.",
                "source_section_or_speaker": "Prepared remarks",
                "extracted_signal": "Management used cautious demand language.",
                "plain_english_label": "Cautious demand language",
                "why_it_matters": "Supports a conservative review read.",
                "ambiguity_note": "Caution is explicit, but no formal withdrawal language is present.",
                "review_priority": "high",
                "has_audio_support": False,
                "audio_row_id": "",
                "audio_summary": "",
                "optional_timestamp": "",
                "display_order": 1,
            }
        ]
    }

    (case_root / "demo" / "fixtures" / f"{case_id}_fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
    (case_root / "demo" / "summary" / "demo_case_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (case_root / "demo" / "summary" / "demo_case_market_context.json").write_text(
        json.dumps(market_context),
        encoding="utf-8",
    )
    (case_root / "demo" / "evidence_rows" / "demo_case_evidence_rows.json").write_text(
        json.dumps(evidence_rows),
        encoding="utf-8",
    )

    payload = load_demo_case_payload(repo_root, case_id)

    assert payload is not None
    assert payload["case_id"] == case_id
    assert payload["joined_audio_rows"] == []
    assert payload["audio_support_available"] is False
    assert payload["artifact_links"]
