from pathlib import Path

from earnings_call_sentiment.demo_case_loader import load_demo_case_catalog, load_demo_case_payload


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_demo_case_catalog_lists_netflix_and_meta() -> None:
    catalog = load_demo_case_catalog(REPO_ROOT)
    case_ids = {row["case_id"] for row in catalog}

    assert "netflix_q1_2022" in case_ids
    assert "meta_q3_2022" in case_ids


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
