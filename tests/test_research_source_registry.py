from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "research" / "ilya_reading_list" / "source_registry.json"
METADATA_PATH = ROOT / "data" / "research" / "ilya_reading_list" / "papers_metadata.json"
VALID_PARSE_STATUSES = {"full_text_parsed", "abstract_only", "source_unavailable", "citation_only"}


def test_source_registry_contains_all_26_papers() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    assert len(registry) == 26
    assert {entry["id"] for entry in registry} == {paper["id"] for paper in metadata}


def test_source_registry_required_fields_and_statuses() -> None:
    required = {
        "id",
        "title",
        "authors",
        "year",
        "canonical_url",
        "arxiv_url",
        "pdf_url",
        "html_url",
        "source_type",
        "license_notes",
        "download_allowed",
        "parse_status",
        "extraction_method",
        "sha256",
        "local_cache_path",
        "committed_text_path",
        "source_confidence",
    }
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in registry:
        assert required <= set(entry)
        assert entry["parse_status"] in VALID_PARSE_STATUSES
        assert entry["source_confidence"] in {"high", "medium", "low"}
        assert entry["license_notes"]
        assert entry["canonical_url"] or entry["pdf_url"] or entry["html_url"]


def test_source_registry_records_full_text_and_limited_sources() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    statuses = {entry["id"]: entry["parse_status"] for entry in registry}
    assert statuses["attention_is_all_you_need"] == "full_text_parsed"
    assert statuses["deep_speech_2_end_to_end_speech_recognition"] == "full_text_parsed"
    assert statuses["kolmogorov_complexity_algorithmic_randomness"] == "citation_only"
