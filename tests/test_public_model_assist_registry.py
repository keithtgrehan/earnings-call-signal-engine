from __future__ import annotations

from pathlib import Path

import yaml

from tools.validate_public_model_assist_registry import validate_registry, validate_registry_payload


ROOT = Path(__file__).resolve().parents[1]


def test_example_public_model_assist_registry_fails_closed_without_cleared_assets() -> None:
    summary = validate_registry(ROOT / "data" / "review" / "public_model_assist_registry.example.yml")

    assert summary["valid"] is True
    assert summary["assets"] == 5
    assert summary["download_performed"] is False
    assert summary["raw_data_committed"] is False
    assert summary["model_weights_committed"] is False
    assert summary["training_enabled_assets"] == []
    assert summary["allowed_weak_review_assist_assets"] == []


def test_unknown_or_blocked_license_cannot_enable_any_use() -> None:
    payload = {
        "assets": [
            {
                "asset_id": "unknown_model",
                "asset_type": "model",
                "name": "Unknown Model",
                "source_url": "https://example.com/model",
                "local_path": "",
                "license": "unknown",
                "license_status": "unknown_fail_closed",
                "permitted_uses": ["weak_review_assist"],
                "blocked_reason": "license not verified",
                "requires_download": False,
                "download_performed": False,
                "raw_data_committed": False,
                "model_weights_committed": False,
                "notes": "fixture",
            },
            {
                "asset_id": "blocked_dataset",
                "asset_type": "dataset",
                "name": "Blocked Dataset",
                "source_url": "https://example.com/data",
                "local_path": "",
                "license": "blocked",
                "license_status": "blocked",
                "permitted_uses": ["benchmark_only"],
                "blocked_reason": "terms not compatible",
                "requires_download": False,
                "download_performed": False,
                "raw_data_committed": False,
                "model_weights_committed": False,
                "notes": "fixture",
            },
        ]
    }

    summary = validate_registry_payload(payload)

    assert summary["valid"] is False
    assert any("unknown_model" in error and "unknown" in error for error in summary["errors"])
    assert any("blocked_dataset" in error and "blocked" in error for error in summary["errors"])


def test_noncommercial_license_and_missing_training_rights_reject_training_use() -> None:
    payload = {
        "assets": [
            {
                "asset_id": "nc_dataset",
                "asset_type": "dataset",
                "name": "Noncommercial Fixture",
                "source_url": "https://example.com/nc",
                "local_path": "",
                "license": "CC-BY-NC-4.0",
                "license_status": "research_only",
                "permitted_uses": ["training"],
                "blocked_reason": "non-commercial license",
                "requires_download": False,
                "download_performed": False,
                "raw_data_committed": False,
                "model_weights_committed": False,
                "notes": "fixture",
            },
            {
                "asset_id": "allowed_without_rights_ref",
                "asset_type": "lexicon",
                "name": "Allowed But Missing Rights Ref",
                "source_url": "https://example.com/lexicon",
                "local_path": "",
                "license": "MIT",
                "license_status": "allowed",
                "permitted_uses": ["training"],
                "blocked_reason": "",
                "requires_download": False,
                "download_performed": False,
                "raw_data_committed": False,
                "model_weights_committed": False,
                "notes": "fixture",
            },
        ]
    }

    summary = validate_registry_payload(payload)

    assert summary["valid"] is False
    assert any("nc_dataset" in error and "non-commercial" in error for error in summary["errors"])
    assert any("allowed_without_rights_ref" in error and "explicit_training_rights_ref" in error for error in summary["errors"])


def test_downloads_and_committed_raw_or_model_files_fail_closed(tmp_path: Path) -> None:
    registry = tmp_path / "registry.yml"
    registry.write_text(
        yaml.safe_dump(
            {
                "assets": [
                    {
                        "asset_id": "downloaded_model",
                        "asset_type": "model",
                        "name": "Downloaded Model",
                        "source_url": "https://example.com/model",
                        "local_path": "/tmp/model",
                        "license": "MIT",
                        "license_status": "allowed",
                        "permitted_uses": ["weak_review_assist"],
                        "blocked_reason": "",
                        "requires_download": True,
                        "download_performed": True,
                        "raw_data_committed": True,
                        "model_weights_committed": True,
                        "notes": "fixture",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    summary = validate_registry(registry, tmp_path / "report.md")

    assert summary["valid"] is False
    assert any("download_performed=true" in error for error in summary["errors"])
    assert any("raw_data_committed=true" in error for error in summary["errors"])
    assert any("model_weights_committed=true" in error for error in summary["errors"])
