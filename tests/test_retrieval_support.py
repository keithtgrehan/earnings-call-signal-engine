from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
import subprocess
import sys

import numpy as np

from earnings_call_sentiment.retrieval_support import (
    build_case_retrieval_rows,
    compute_embeddings,
    load_retrieval_bundle,
    search_retrieval_rows,
    write_retrieval_bundle,
    write_retrieval_readme,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _netflix_retrieval_bundle():
    return load_retrieval_bundle(_repo_root() / "data" / "demo_cases" / "netflix_q1_2022" / "demo" / "retrieval")


def _load_netflix_eval_fixture() -> dict[str, object]:
    path = _repo_root() / "tests" / "fixtures" / "netflix_retrieval_eval.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(json.dumps(value) if isinstance(value, str) else str(value) for value in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _make_fake_case(tmp_path: Path) -> Path:
    case_root = tmp_path / "demo_case"
    transcript_blocks = [
        {
            "section": "presentation",
            "speaker": "Host",
            "speaker_role": "management",
            "text": "Welcome to the quarter.",
            "block_id": 0,
        },
        {
            "section": "question_and_answer",
            "speaker": "Analyst A",
            "speaker_role": "analyst",
            "text": "Why did revenue growth slow and guidance come down?",
            "block_id": 1,
        },
        {
            "section": "question_and_answer",
            "speaker": "CEO",
            "speaker_role": "management",
            "text": "Competition increased and churn stayed a little higher than we expected.",
            "block_id": 2,
        },
        {
            "section": "question_and_answer",
            "speaker": "CFO",
            "speaker_role": "management",
            "text": "We still expect margin improvement later in the year.",
            "block_id": 3,
        },
    ]
    _write_json(
        case_root / "processed" / "transcript_text" / "transcript_sectioned.json",
        {"blocks": transcript_blocks},
    )
    _write_json(
        case_root / "processed" / "chunks" / "segment_metadata.json",
        {
            "segments": [
                {
                    "segment_id": 0,
                    "block_id": 0,
                    "section": "presentation",
                    "speaker": "Host",
                    "speaker_role": "management",
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Welcome to the quarter.",
                },
                {
                    "segment_id": 1,
                    "block_id": 1,
                    "section": "question_and_answer",
                    "speaker": "Analyst A",
                    "speaker_role": "analyst",
                    "start": 5.0,
                    "end": 10.0,
                    "text": "Why did revenue growth slow and guidance come down?",
                },
                {
                    "segment_id": 2,
                    "block_id": 2,
                    "section": "question_and_answer",
                    "speaker": "CEO",
                    "speaker_role": "management",
                    "start": 10.0,
                    "end": 15.0,
                    "text": "Competition increased and churn stayed a little higher than we expected.",
                },
                {
                    "segment_id": 3,
                    "block_id": 3,
                    "section": "question_and_answer",
                    "speaker": "CFO",
                    "speaker_role": "management",
                    "start": 15.0,
                    "end": 20.0,
                    "text": "We still expect margin improvement later in the year.",
                },
            ]
        },
    )
    _write_jsonl(
        case_root / "processed" / "chunks" / "chunks_scored.jsonl",
        [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Welcome to the quarter.",
                "sentiment": "POSITIVE",
                "score": 0.9,
                "signed_score": 0.9,
            },
            {
                "start": 5.0,
                "end": 10.0,
                "text": "Why did revenue growth slow and guidance come down?",
                "sentiment": "NEGATIVE",
                "score": 0.8,
                "signed_score": -0.8,
            },
            {
                "start": 10.0,
                "end": 15.0,
                "text": "Competition increased and churn stayed a little higher than we expected.",
                "sentiment": "NEGATIVE",
                "score": 0.85,
                "signed_score": -0.85,
            },
            {
                "start": 15.0,
                "end": 20.0,
                "text": "We still expect margin improvement later in the year.",
                "sentiment": "POSITIVE",
                "score": 0.7,
                "signed_score": 0.7,
            },
        ],
    )
    _write_csv(
        case_root / "processed" / "signals" / "guidance.csv",
        [
            "start",
            "end",
            "text",
            "sentiment",
            "score",
            "topic",
            "period",
            "numbers",
            "numeric_signature",
            "midpoint_hint",
            "guidance_strength",
            "count_numbers",
            "has_percent",
            "has_range",
            "has_currency",
            "matched_cues",
        ],
        [
            [
                10.0,
                15.0,
                "Competition increased and churn stayed a little higher than we expected.",
                "NEGATIVE",
                0.85,
                "outlook",
                "Q2",
                "",
                "",
                "",
                0.9,
                0,
                False,
                False,
                False,
                "guidance;q2",
            ]
        ],
    )
    _write_json(
        case_root / "processed" / "signals" / "shareholder_letter_evidence.json",
        {
            "schema_version": "1.0.0",
            "paragraph_count": 2,
            "evidence": {
                "growth_slowdown": "Revenue growth slowed because competition and macro pressure increased.",
                "competitive_and_macro_headwinds": "Revenue growth slowed because competition and macro pressure increased.",
            },
        },
    )
    (case_root / "processed" / "transcript_text" / "shareholder_letter_text.txt").parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    (
        case_root / "processed" / "transcript_text" / "shareholder_letter_text.txt"
    ).write_text(
        "Revenue growth slowed because competition and macro pressure increased.\n\n"
        "We still believe the margin profile can improve over time.\n",
        encoding="utf-8",
    )
    return case_root


def test_build_case_retrieval_rows_preserves_provenance(tmp_path: Path) -> None:
    case_root = _make_fake_case(tmp_path)

    rows = build_case_retrieval_rows(case_root)

    by_row_id = {row["row_id"]: row for row in rows}
    assert by_row_id["transcript_chunk_0002"]["chunk_id"] == "segment_0002"
    assert by_row_id["transcript_chunk_0002"]["supporting_only"] is True
    assert by_row_id["qa_pair_001_question"]["source_locator"] == "qa_pair_id:1/question/block_id:1"
    assert by_row_id["qa_pair_001_question"]["start_time_s"] == 5.0
    assert by_row_id["qa_pair_001_answer"]["metadata"]["block_ids"] == [2, 3]
    assert by_row_id["qa_pair_001_answer"]["start_time_s"] == 10.0
    assert by_row_id["qa_pair_001_answer"]["end_time_s"] == 20.0
    assert by_row_id["guidance_span_001"]["chunk_id"] == "segment_0002"
    assert by_row_id["guidance_span_001"]["plain_english_label"].startswith("guidance pressure")
    assert by_row_id["shareholder_letter_paragraph_001"]["deterministic_category"] == "competitive_and_macro_headwinds"


def test_write_and_load_retrieval_bundle_round_trip(tmp_path: Path) -> None:
    case_root = _make_fake_case(tmp_path)
    rows = build_case_retrieval_rows(case_root)

    paths = write_retrieval_bundle(
        case_root=case_root,
        rows=rows,
        out_dir=tmp_path / "bundle",
        include_embeddings=False,
    )
    readme_path = write_retrieval_readme(case_root=case_root, out_dir=tmp_path / "bundle")
    bundle = load_retrieval_bundle(tmp_path / "bundle")

    assert paths["rows"].exists()
    assert paths["manifest"].exists()
    assert readme_path.exists()
    assert bundle.manifest["embedding"]["status"] == "not_written"
    assert len(bundle.rows) == len(rows)
    assert bundle.embeddings is None


def test_lexical_search_prefers_pressure_guidance_rows() -> None:
    rows = [
        {
            "row_id": "generic_guidance",
            "case_id": "demo",
            "source_type": "guidance_span",
            "source_locator": "guidance_row:1",
            "text": "Always good to provide that nonguidance guidance.",
            "plain_english_label": "guidance span / outlook / unknown",
            "deterministic_category": "guidance:outlook:unknown",
            "supporting_only": True,
        },
        {
            "row_id": "pressure_guidance",
            "case_id": "demo",
            "source_type": "guidance_span",
            "source_locator": "guidance_row:2",
            "text": "We missed the quarter and expect softer demand with higher churn.",
            "plain_english_label": "guidance pressure / outlook / q2",
            "deterministic_category": "guidance:outlook:q2",
            "supporting_only": True,
        },
    ]

    results, _ = search_retrieval_rows(
        query="guidance pressure moments",
        rows=rows,
        top_k=2,
        mode="lexical",
    )

    assert results[0].row["row_id"] == "pressure_guidance"


def test_search_falls_back_to_lexical_when_embeddings_are_missing() -> None:
    rows = [
        {
            "row_id": "alpha",
            "case_id": "demo",
            "source_type": "qa_answer_span",
            "source_locator": "qa_pair_id:1/answer",
            "text": "The rollout will be gradual.",
            "plain_english_label": "management answer span",
            "deterministic_category": "management_answer",
            "supporting_only": True,
        }
    ]

    results, notes = search_retrieval_rows(
        query="gradual rollout",
        rows=rows,
        top_k=1,
        mode="hybrid",
        row_embeddings=None,
    )

    assert results[0].retrieval_mode == "lexical"
    assert any("falling back to lexical" in note for note in notes)


def test_semantic_search_uses_injected_query_embedding() -> None:
    rows = [
        {
            "row_id": "row_a",
            "case_id": "demo",
            "source_type": "analyst_question_span",
            "source_locator": "a",
            "text": "Advertising question",
            "plain_english_label": "analyst question span",
            "deterministic_category": "analyst_question",
            "supporting_only": True,
        },
        {
            "row_id": "row_b",
            "case_id": "demo",
            "source_type": "qa_answer_span",
            "source_locator": "b",
            "text": "Margin answer",
            "plain_english_label": "management answer span",
            "deterministic_category": "management_answer",
            "supporting_only": True,
        },
    ]
    row_embeddings = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    query_embedding = np.asarray([0.0, 1.0], dtype=np.float32)

    results, _ = search_retrieval_rows(
        query="ignored",
        rows=rows,
        top_k=2,
        mode="semantic",
        row_embeddings=row_embeddings,
        query_embedding=query_embedding,
    )

    assert results[0].row["row_id"] == "row_b"
    assert results[0].semantic_score is not None


def test_netflix_reference_case_output_shape() -> None:
    case_root = _repo_root() / "data" / "demo_cases" / "netflix_q1_2022"

    rows = build_case_retrieval_rows(case_root)

    source_types = {row["source_type"] for row in rows}
    assert len(rows) >= 200
    assert {
        "transcript_chunk",
        "analyst_question_span",
        "qa_answer_span",
        "guidance_span",
        "shareholder_letter_paragraph",
    }.issubset(source_types)
    assert all(row["supporting_only"] is True for row in rows)
    assert any(row["source_type"] == "guidance_span" and row["chunk_id"] for row in rows)
    assert any(row["source_type"] == "shareholder_letter_paragraph" and row["deterministic_category"] for row in rows)


def test_build_case_retrieval_cli_smoke(tmp_path: Path) -> None:
    case_root = _make_fake_case(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_case_retrieval.py",
            "--case-root",
            str(case_root),
            "--out-dir",
            str(tmp_path / "bundle"),
            "--no-embeddings",
        ],
        cwd=_repo_root(),
        env=os.environ | {"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )

    assert "row_count=" in result.stdout
    assert (tmp_path / "bundle").exists()


def test_search_case_retrieval_cli_smoke(tmp_path: Path) -> None:
    case_root = _make_fake_case(tmp_path)
    rows = build_case_retrieval_rows(case_root)
    write_retrieval_bundle(
        case_root=case_root,
        rows=rows,
        out_dir=tmp_path / "bundle",
        include_embeddings=False,
    )
    write_retrieval_readme(case_root=case_root, out_dir=tmp_path / "bundle")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/search_case_retrieval.py",
            "guidance pressure",
            "--bundle-dir",
            str(tmp_path / "bundle"),
            "--mode",
            "lexical",
            "--top-k",
            "2",
        ],
        cwd=_repo_root(),
        env=os.environ | {"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Supporting-only retrieval output" in result.stdout
    assert "requested_mode=lexical" in result.stdout


def test_search_case_retrieval_cli_supports_query_flag_and_case_alias(tmp_path: Path) -> None:
    case_root = _make_fake_case(tmp_path)
    rows = build_case_retrieval_rows(case_root)
    write_retrieval_bundle(
        case_root=case_root,
        rows=rows,
        out_dir=tmp_path / "bundle",
        include_embeddings=False,
    )
    write_retrieval_readme(case_root=case_root, out_dir=tmp_path / "bundle")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/search_case_retrieval.py",
            "--query",
            "guidance pressure",
            "--case",
            "demo_case",
            "--bundle-dir",
            str(tmp_path / "bundle"),
            "--mode",
            "hybrid",
            "--top-k",
            "2",
        ],
        cwd=_repo_root(),
        env=os.environ | {"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )

    assert "case_id=demo_case" in result.stdout
    assert "requested_mode=hybrid" in result.stdout
    assert "falling back to lexical retrieval" in result.stdout


def test_search_case_retrieval_help_mentions_hybrid_reviewer_mode() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/search_case_retrieval.py",
            "--help",
        ],
        cwd=_repo_root(),
        env=os.environ | {"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Hybrid is the recommended" in result.stdout
    assert "fallback/debug modes" in result.stdout
    assert "Use hybrid for reviewer workflows" in result.stdout
    assert "--case-id" in result.stdout
    assert "--case" in result.stdout
    assert "--query" in result.stdout


def test_netflix_retrieval_eval_fixture_is_bounded() -> None:
    fixture = _load_netflix_eval_fixture()

    assert fixture["case_id"] == "netflix_q1_2022"
    assert fixture["recommended_mode"] == "hybrid"
    assert 8 <= len(fixture["queries"]) <= 12


def test_netflix_retrieval_eval_fixture_matches_reviewer_queries() -> None:
    fixture = _load_netflix_eval_fixture()
    bundle = _netflix_retrieval_bundle()
    query_specs = fixture["queries"]
    queries = [spec["query"] for spec in query_specs]
    model_name = bundle.manifest["embedding"]["model_name"]
    query_embeddings = None
    mode = "lexical"

    if bundle.embeddings is not None:
        try:
            query_embeddings = compute_embeddings(
                queries,
                model_name=model_name,
                device="cpu",
                local_files_only=True,
            )
            mode = str(fixture["recommended_mode"])
        except Exception:
            query_embeddings = None

    for index, spec in enumerate(query_specs):
        results, _ = search_retrieval_rows(
            query=spec["query"],
            rows=bundle.rows,
            top_k=int(spec.get("top_k", fixture["top_k"])),
            mode=mode,
            row_embeddings=(bundle.embeddings if mode == "hybrid" else None),
            query_embedding=(query_embeddings[index] if query_embeddings is not None else None),
            model_name=model_name,
            device="cpu",
        )

        assert results, spec["query"]

        row_ids = [str(result.row["row_id"]) for result in results]
        source_types = [str(result.row["source_type"]) for result in results]

        expected_first_source_type = spec.get("expected_first_source_type")
        if expected_first_source_type:
            assert source_types[0] == expected_first_source_type, spec["query"]

        for expected_source_type in spec.get("expected_source_types", []):
            assert expected_source_type in source_types, spec["query"]

        expected_any_row_ids = set(spec.get("expected_any_row_ids", []))
        if expected_any_row_ids:
            assert expected_any_row_ids & set(row_ids), spec["query"]

        for excluded_row_id in spec.get("excluded_row_ids", []):
            assert excluded_row_id not in row_ids, spec["query"]
