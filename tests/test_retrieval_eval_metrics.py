from __future__ import annotations

import csv
import json
from pathlib import Path

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects, summarize_retrieval_results, write_jsonl
from tools.evaluate_retrieval import _gate_status, main as retrieval_eval_main


def test_retrieval_eval_metrics_from_objects(tmp_path: Path) -> None:
    objects = tmp_path / "objects.csv"
    fields = ["object_id", "object_type", "case_id", "ticker", "company", "fiscal_period", "source_type", "source_ref", "section", "speaker", "topic", "span_start_char", "span_end_char", "source_sha256", "text_sha256", "normalized_transcript_sha256", "provenance_hash", "rights_tier", "retrieval_priority", "commit_allowed", "raw_text_commit_allowed", "raw_text_committed"]
    with objects.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"object_id": "obj1", "object_type": "event_aligned_chunk", "case_id": "hd_2025_q4", "ticker": "HD", "company": "", "fiscal_period": "2025 Q4", "source_type": "chunk", "source_ref": "/desktop/chunk.txt", "section": "prepared_remarks", "speaker": "management", "topic": "guidance", "span_start_char": "0", "span_end_char": "10", "source_sha256": "sha256:" + "a" * 64, "text_sha256": "sha256:" + "b" * 64, "normalized_transcript_sha256": "sha256:" + "c" * 64, "provenance_hash": "sha256:" + "d" * 64, "rights_tier": "safe_to_download", "retrieval_priority": "2", "commit_allowed": "false", "raw_text_commit_allowed": "false", "raw_text_committed": "false"})
    queries = tmp_path / "queries.jsonl"
    write_jsonl(
        queries,
        [
            {
                "query_id": "q1",
                "query_text": "HD guidance management",
                "query_intent": "prepared_guidance",
                "target_case_id": "hd_2025_q4",
                "target_ticker": "HD",
                "target_fiscal_period": "2025 Q4",
                "expected_object_types": ["event_aligned_chunk"],
                "expected_signal_types": ["guidance"],
                "expected_sections": ["prepared_remarks"],
                "expected_speaker_roles": ["management"],
                "expected_evidence_ids": ["obj1"],
                "negative_control": False,
                "abstention_expected": False,
                "rights_required": ["normalized_transcript_manifest", "retrieval_object_manifest"],
                "notes": "metadata-only smoke row",
            },
            {
                "query_id": "q2",
                "query_text": "HD unsupported request",
                "query_intent": "trading_request",
                "target_case_id": "hd_2025_q4",
                "target_ticker": "HD",
                "target_fiscal_period": "2025 Q4",
                "expected_object_types": [],
                "expected_signal_types": [],
                "expected_sections": [],
                "expected_speaker_roles": [],
                "expected_evidence_ids": [],
                "negative_control": True,
                "abstention_expected": True,
                "rights_required": ["retrieval_object_manifest"],
                "notes": "must abstain",
            },
        ],
    )
    summary = evaluate_retrieval_objects(objects, queries)
    assert summary["recall_at_1"] == 1.0
    assert summary["rates"]["recall_at_1"] == {"numerator": 1, "denominator": 1, "percentage": 100.0}
    assert summary["rates"]["abstention_correctness"] == {"numerator": 1, "denominator": 1, "percentage": 100.0}
    assert summary["raw_text_returned"] is False


def test_evaluated_rag_gate_blocks_fallback_overuse() -> None:
    assert not _gate_status(
        {
            "query_count": 10,
            "recall_at_1": 1.0,
            "citation_validity": 1.0,
            "invalid_citation_rate": 0.0,
            "wrong_case_ticker_period": 0,
            "fallback_overuse": 0.9,
            "abstention_correctness": 1.0,
            "provenance_completeness": 1.0,
            "raw_text_returned": False,
            "manifest_status": "completed",
            "placeholder_expected_ids": 0,
        }
    )


def test_fallback_overuse_rate_increments_for_semantic_fallback_result() -> None:
    query = {
        "query_id": "q1",
        "query_text": "HD guidance metadata",
        "query_intent": "prepared_guidance",
        "target_case_id": "hd_2025_q4",
        "target_ticker": "HD",
        "target_fiscal_period": "2025 Q4",
        "expected_object_types": ["evidence_object"],
        "expected_signal_types": ["guidance"],
        "expected_sections": ["prepared_remarks"],
        "expected_speaker_roles": ["management"],
        "expected_evidence_ids": ["obj1"],
        "negative_control": False,
        "abstention_expected": False,
        "rights_required": ["retrieval_object_manifest"],
        "notes": "metadata-only fallback overuse regression row",
    }
    result = {
        "query_id": "q1",
        "result_rank": 1,
        "object_id": "fallback1",
        "object_type": "semantic_fallback",
        "case_id": "hd_2025_q4",
        "ticker": "HD",
        "fiscal_period": "2025 Q4",
        "source_hash": "sha256:" + "a" * 64,
        "normalized_transcript_hash": "sha256:" + "b" * 64,
        "provenance_hash": "sha256:" + "c" * 64,
        "section_label": "prepared_remarks",
        "speaker_role": "management",
        "qa_pair_id": "",
        "retrieval_score": 0.4,
        "retrieval_method": "manual_fixture",
        "citation_valid": True,
        "raw_text_returned": False,
        "blocked_reason": None,
        "notes": "metadata-only semantic fallback result",
    }

    summary = summarize_retrieval_results(queries=[query], results=[result], smoke_metrics=True)

    assert summary["rates"]["fallback_overuse_rate"] == {"numerator": 1, "denominator": 1, "percentage": 100.0}
    assert summary["fallback_overuse"] == 1.0


def test_production_metrics_fail_closed_when_placeholders_remain(tmp_path: Path) -> None:
    queries = tmp_path / "queries.jsonl"
    write_jsonl(
        queries,
        [
            {
                "query_id": "q1",
                "query_text": "HD guidance metadata",
                "query_intent": "prepared_guidance",
                "target_case_id": "hd_2025_q4",
                "target_ticker": "HD",
                "target_fiscal_period": "2025 Q4",
                "expected_object_types": ["evidence_object"],
                "expected_signal_types": ["guidance"],
                "expected_sections": ["prepared_remarks"],
                "expected_speaker_roles": ["management"],
                "expected_evidence_ids": ["REVIEW_REQUIRED_HD_2025_Q4_EVIDENCE_ID"],
                "negative_control": False,
                "abstention_expected": False,
                "rights_required": ["retrieval_object_manifest"],
                "notes": "placeholder must block production metrics",
            }
        ],
    )
    objects = tmp_path / "objects.csv"
    objects.write_text(
        "object_id,object_type,case_id,ticker,company,fiscal_period,source_type,source_ref,section,speaker,topic,source_sha256,text_sha256,normalized_transcript_sha256,provenance_hash,rights_tier,retrieval_priority,commit_allowed,raw_text_commit_allowed,raw_text_committed\n",
        encoding="utf-8",
    )

    code = retrieval_eval_main(
        [
            "--mode",
            "production",
            "--queries",
            str(queries),
            "--objects",
            str(objects),
            "--results-out",
            str(tmp_path / "results.jsonl"),
            "--summary-json",
            str(tmp_path / "summary.json"),
            "--summary-md",
            str(tmp_path / "summary.md"),
        ]
    )

    assert code == 1
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["evaluated_rag"] is False
    assert any("placeholder" in failure for failure in summary["failures"])
