from __future__ import annotations

from signal_engine.training.sources import build_training_candidate_manifest, validate_training_source_rows


def test_external_training_source_cannot_train_or_write_gold() -> None:
    rows = [
        {
            "source_id": "project_human_gold_labels",
            "source_type": "project_gold",
            "default_mode": "supervised_training_candidate",
            "training_allowed": True,
            "writes_gold": False,
            "weak_labels_can_be_gold": False,
            "rights_status": "project_validated_required",
            "source_reference": "data/gold/gold_labels.jsonl",
        },
        {
            "source_id": "financebench",
            "source_type": "external_dataset",
            "default_mode": "benchmark_only",
            "training_allowed": True,
            "writes_gold": True,
            "weak_labels_can_be_gold": False,
            "rights_status": "review_required",
            "source_reference": "https://arxiv.org/abs/2311.11944",
        },
    ]
    errors = validate_training_source_rows(rows)
    assert "row 2: external sources cannot allow training by default" in errors
    assert "row 2: training sources cannot write gold labels" in errors


def test_training_candidate_manifest_separates_benchmark_sources() -> None:
    rows = [
        {
            "source_id": "project_human_gold_labels",
            "source_type": "project_gold",
            "default_mode": "supervised_training_candidate",
            "training_allowed": True,
            "writes_gold": False,
            "weak_labels_can_be_gold": False,
            "rights_status": "project_validated_required",
            "source_reference": "data/gold/gold_labels.jsonl",
        },
        {
            "source_id": "ectsum",
            "source_type": "external_dataset",
            "default_mode": "benchmark_only",
            "training_allowed": False,
            "writes_gold": False,
            "weak_labels_can_be_gold": False,
            "rights_status": "review_required",
            "source_reference": "https://arxiv.org/abs/2210.12467",
        },
    ]
    manifest = build_training_candidate_manifest(rows)
    assert len(manifest["supervised_gold_candidates"]) == 1
    assert len(manifest["benchmark_only_sources"]) == 1
