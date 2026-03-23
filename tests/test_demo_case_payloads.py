from earnings_call_sentiment.demo_case_payloads import (
    build_demo_fixture_index,
    inject_market_context,
    normalize_demo_evidence_rows,
    normalize_demo_joined_audio_rows,
    normalize_demo_market_context,
)


def test_normalize_demo_evidence_rows_trims_netflix_and_lightens_audio() -> None:
    rows = [
        {
            "row_id": "transcript_growth_headwinds",
            "source": "transcript",
            "section": "question_and_answer",
            "speaker": "Reed Hastings",
            "raw_excerpt": "Growth slowed.",
            "extracted_signal": "growth pressure",
            "plain_english_label": "management acknowledged growth pressure",
            "why_it_matters": "important",
            "remaining_ambiguity": "still unclear",
            "review_priority": "high",
            "optional_audio_support": {
                "row_id": "qa_growth_headwinds_audio",
                "plain_english_audio_summary": "opened after a pause",
            },
            "optional_timestamp": "00:32-03:16",
        },
        {
            "row_id": "transcript_account_sharing_monetization",
            "source": "transcript",
            "section": "question_and_answer",
            "speaker": "Reed Hastings",
            "raw_excerpt": "Account sharing.",
            "extracted_signal": "account sharing",
            "plain_english_label": "account sharing moved into the core monetization narrative",
            "why_it_matters": "dup row",
            "remaining_ambiguity": "still qualified",
            "review_priority": "medium",
        },
        {
            "row_id": "letter_growth_slowdown",
            "source": "shareholder_letter",
            "raw_excerpt": "Letter slowdown.",
            "extracted_signal": "growth slowdown",
            "plain_english_label": "growth slowdown",
            "why_it_matters": "letter context",
            "remaining_ambiguity": "authored framing",
            "review_priority": "medium",
        },
        {
            "row_id": "letter_headwinds",
            "source": "shareholder_letter",
            "raw_excerpt": "Headwinds.",
            "extracted_signal": "headwinds",
            "plain_english_label": "competitive and macro headwinds",
            "why_it_matters": "letter context",
            "remaining_ambiguity": "authored framing",
            "review_priority": "medium",
        },
        {
            "row_id": "letter_margin_framing",
            "source": "shareholder_letter",
            "raw_excerpt": "Margins.",
            "extracted_signal": "margin framing",
            "plain_english_label": "forward margin framing",
            "why_it_matters": "letter context",
            "remaining_ambiguity": "authored framing",
            "review_priority": "medium",
        },
        {
            "row_id": "financial_context_q1_2022",
            "source": "financials",
            "section": "income_statement",
            "raw_excerpt": "Financial context.",
            "extracted_signal": "reported quarter",
            "plain_english_label": "quarter anchored by reported financials",
            "why_it_matters": "anchored",
            "remaining_ambiguity": "context only",
            "review_priority": "medium",
        },
        {
            "row_id": "transcript_q2_paid_net_adds_guide",
            "source": "transcript",
            "section": "question_and_answer",
            "speaker": "Spencer Neumann",
            "raw_excerpt": "Paid net adds.",
            "extracted_signal": "miss explained",
            "plain_english_label": "management explained the miss directly",
            "why_it_matters": "important",
            "remaining_ambiguity": "recovery qualified",
            "review_priority": "high",
        },
        {
            "row_id": "transcript_ad_supported_option",
            "source": "transcript",
            "section": "question_and_answer",
            "speaker": "Reed Hastings",
            "raw_excerpt": "Ad tier.",
            "extracted_signal": "future path",
            "plain_english_label": "qualified answer on the ad-supported option",
            "why_it_matters": "important",
            "remaining_ambiguity": "not launched",
            "review_priority": "high",
        },
    ]

    normalized = normalize_demo_evidence_rows("netflix_q1_2022", rows)

    assert [row["row_id"] for row in normalized] == [
        "transcript_growth_headwinds",
        "transcript_q2_paid_net_adds_guide",
        "transcript_ad_supported_option",
        "letter_growth_slowdown",
        "letter_headwinds",
        "letter_margin_framing",
        "financial_context_q1_2022",
    ]
    assert normalized[0]["source_section_or_speaker"] == "Reed Hastings / Q&A"
    assert normalized[0]["has_audio_support"] is True
    assert normalized[0]["audio_row_id"] == "qa_growth_headwinds_audio"
    assert normalized[0]["audio_summary"] == "opened after a pause"


def test_normalize_demo_joined_audio_rows_keeps_only_ui_fields() -> None:
    rows = [
        {
            "row_id": "qa_capex_ai_pressure_audio",
            "plain_english_label": "analyst pushback on AI capex",
            "analyst_question_excerpt": "question",
            "management_answer_excerpt": "answer",
            "plain_english_interpretation": "interpretation",
            "plain_english_audio_summary": "summary",
            "transcript_hedge_markers": ["we expect"],
            "question_time_range": "25:10-26:03",
            "answer_time_range": "26:02-28:00",
            "review_priority": "high",
            "qa_shift_delta": 1.2,
            "filler_count": 3,
        }
    ]

    normalized = normalize_demo_joined_audio_rows("meta_q3_2022", rows)

    assert normalized == [
        {
            "row_id": "qa_capex_ai_pressure_audio",
            "case_id": "meta_q3_2022",
            "plain_english_label": "analyst pushback on AI capex",
            "analyst_question_excerpt": "question",
            "management_answer_excerpt": "answer",
            "plain_english_interpretation": "interpretation",
            "plain_english_audio_summary": "summary",
            "transcript_hedge_markers": ["we expect"],
            "question_time_range": "25:10-26:03",
            "answer_time_range": "26:02-28:00",
            "review_priority": "high",
        }
    ]


def test_market_context_and_fixture_index_are_normalized() -> None:
    market_context = {
        "case_id": "meta_q3_2022",
        "company": "Meta Platforms",
        "quarter": "Q3 2022",
        "event_date": "2022-10-26",
        "key_extracted_signals": ["signal"],
        "market_reaction_window": {"reaction_direction": "negative"},
        "market_reaction_note": "reaction note",
        "source": {"pricing_url": "https://prices", "coverage_url": "https://coverage"},
        "caveat": "Context only.",
    }
    normalized_market = normalize_demo_market_context(market_context)
    summary = inject_market_context({"case_id": "meta_q3_2022"}, normalized_market)
    fixture = build_demo_fixture_index(
        case_id="meta_q3_2022",
        company="Meta Platforms",
        quarter="Q3 2022",
        case_status="ready",
        artifact_paths={"evidence_rows": "demo/evidence_rows/meta_q3_2022_evidence_rows.json"},
        preview_row_ids=["one", "two"],
        notes=["note"],
    )

    assert normalized_market["source"] == {
        "primary_url": "https://prices",
        "secondary_url": "https://coverage",
    }
    assert summary["market_context"]["panel_title"] == "Market context around the Q3 2022 release window"
    assert fixture == {
        "case_id": "meta_q3_2022",
        "company": "Meta Platforms",
        "quarter": "Q3 2022",
        "case_status": "ready",
        "artifact_paths": {"evidence_rows": "demo/evidence_rows/meta_q3_2022_evidence_rows.json"},
        "preview_row_ids": ["one", "two"],
        "notes": ["note"],
    }
