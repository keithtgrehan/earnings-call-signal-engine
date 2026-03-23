from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.demo_case_payloads import (
    build_demo_fixture_index,
    inject_market_context,
    normalize_demo_evidence_rows,
    normalize_demo_joined_audio_rows,
    normalize_demo_market_context,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_CASES = ROOT / "data" / "demo_cases"

CASE_CONFIGS = [
    {
        "case_id": "netflix_q1_2022",
        "company": "Netflix",
        "quarter": "Q1 2022",
        "evidence_paths": [
            DEMO_CASES / "netflix_q1_2022" / "demo" / "evidence_rows" / "netflix_q1_2022_evidence_rows.json",
            DEMO_CASES / "netflix_q1_2022" / "demo" / "evidence_rows" / "netflix_demo_evidence_rows.json",
        ],
        "joined_path": DEMO_CASES / "netflix_q1_2022" / "processed" / "joined_review" / "joined_qa_audio_review.json",
        "market_path": DEMO_CASES / "netflix_q1_2022" / "demo" / "summary" / "netflix_q1_2022_market_context.json",
        "summary_paths": [
            DEMO_CASES / "netflix_q1_2022" / "demo" / "summary" / "netflix_q1_2022_summary.json",
            DEMO_CASES / "netflix_q1_2022" / "demo" / "summary" / "netflix_demo_summary.json",
        ],
        "fixture_paths": [
            DEMO_CASES / "netflix_q1_2022" / "demo" / "fixtures" / "netflix_q1_2022_fixture.json",
            DEMO_CASES / "netflix_q1_2022" / "demo" / "fixtures" / "netflix_demo_fixture.json",
        ],
    },
    {
        "case_id": "meta_q3_2022",
        "company": "Meta Platforms",
        "quarter": "Q3 2022",
        "evidence_paths": [
            DEMO_CASES / "meta_q3_2022" / "demo" / "evidence_rows" / "meta_q3_2022_evidence_rows.json",
            DEMO_CASES / "meta_q3_2022" / "demo" / "evidence_rows" / "meta_demo_evidence_rows.json",
        ],
        "joined_path": DEMO_CASES / "meta_q3_2022" / "processed" / "joined_review" / "joined_qa_audio_review.json",
        "market_path": DEMO_CASES / "meta_q3_2022" / "demo" / "summary" / "meta_q3_2022_market_context.json",
        "summary_paths": [
            DEMO_CASES / "meta_q3_2022" / "demo" / "summary" / "meta_q3_2022_summary.json",
            DEMO_CASES / "meta_q3_2022" / "demo" / "summary" / "meta_demo_summary.json",
        ],
        "fixture_paths": [
            DEMO_CASES / "meta_q3_2022" / "demo" / "fixtures" / "meta_q3_2022_fixture.json",
            DEMO_CASES / "meta_q3_2022" / "demo" / "fixtures" / "meta_demo_fixture.json",
        ],
    },
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalize_case(config: dict) -> None:
    evidence_source = load_json(config["evidence_paths"][0])
    joined_source = load_json(config["joined_path"])
    market_source = load_json(config["market_path"])
    fixture_source = load_json(config["fixture_paths"][0])

    normalized_evidence = {"rows": normalize_demo_evidence_rows(config["case_id"], evidence_source.get("rows", []))}
    normalized_joined = {"rows": normalize_demo_joined_audio_rows(config["case_id"], joined_source.get("rows", []))}
    normalized_market = normalize_demo_market_context(market_source)
    normalized_fixture = build_demo_fixture_index(
        case_id=config["case_id"],
        company=config["company"],
        quarter=config["quarter"],
        case_status=fixture_source.get("case_status", "ready"),
        artifact_paths=fixture_source.get("artifact_paths", {}),
        preview_row_ids=[row["row_id"] for row in normalized_evidence["rows"][:6]],
        notes=fixture_source.get("notes", []),
    )

    for path in config["evidence_paths"]:
        write_json(path, normalized_evidence)
    write_json(config["joined_path"], normalized_joined)
    write_json(config["market_path"], normalized_market)

    for path in config["summary_paths"]:
        summary = inject_market_context(load_json(path), normalized_market)
        write_json(path, summary)

    for path in config["fixture_paths"]:
        write_json(path, normalized_fixture)


def main() -> None:
    for config in CASE_CONFIGS:
        normalize_case(config)
        print(f"Normalized {config['case_id']}")


if __name__ == "__main__":
    main()
