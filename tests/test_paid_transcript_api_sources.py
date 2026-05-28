from __future__ import annotations

import csv
from pathlib import Path

from tools.discover_paid_transcript_api_sources import run_discovery


def _write_config(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_disabled_provider_writes_skipped_report_and_exits_zero(tmp_path: Path) -> None:
    config = tmp_path / "providers.yml"
    report = tmp_path / "report.md"
    out_csv = tmp_path / "candidates.csv"
    _write_config(
        config,
        """
providers:
  - provider_name: FixtureProvider
    enabled: false
    api_key_env_var: FIXTURE_API_KEY
    base_url: https://api.example.com/transcripts
    license_config_ref: ""
    allow_raw_storage: false
    allow_eval_use: false
    allow_training_use: false
""",
    )

    summary = run_discovery(config_path=config, out_csv=out_csv, report_path=report)

    assert summary["providers_skipped"] == 1
    assert summary["candidates_written"] == 0
    assert "disabled" in report.read_text(encoding="utf-8").lower()


def test_missing_api_key_writes_skipped_report_and_exits_zero(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("FIXTURE_API_KEY", raising=False)
    config = tmp_path / "providers.yml"
    report = tmp_path / "report.md"
    out_csv = tmp_path / "candidates.csv"
    _write_config(
        config,
        """
providers:
  - provider_name: FixtureProvider
    enabled: true
    api_key_env_var: FIXTURE_API_KEY
    base_url: https://api.example.com/transcripts
    license_config_ref: license://fixture
    allow_raw_storage: false
    allow_eval_use: false
    allow_training_use: false
""",
    )

    summary = run_discovery(config_path=config, out_csv=out_csv, report_path=report)

    assert summary["providers_skipped"] == 1
    assert "missing api key" in report.read_text(encoding="utf-8").lower()


def test_enabled_provider_without_license_is_blocked_without_raw_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FIXTURE_API_KEY", "test-key")
    config = tmp_path / "providers.yml"
    report = tmp_path / "report.md"
    out_csv = tmp_path / "candidates.csv"
    _write_config(
        config,
        """
providers:
  - provider_name: FixtureProvider
    enabled: true
    api_key_env_var: FIXTURE_API_KEY
    base_url: https://api.example.com/transcripts
    license_config_ref: ""
    allow_raw_storage: false
    allow_eval_use: false
    allow_training_use: false
""",
    )

    summary = run_discovery(config_path=config, out_csv=out_csv, report_path=report)

    assert summary["providers_blocked"] == 1
    assert summary["candidates_written"] == 0
    assert not list(tmp_path.glob("*.txt"))
    assert "license_config_ref" in report.read_text(encoding="utf-8")


def test_generated_metadata_candidates_contain_no_transcript_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FIXTURE_API_KEY", "test-key")
    config = tmp_path / "providers.yml"
    report = tmp_path / "report.md"
    out_csv = tmp_path / "candidates.csv"
    raw_phrase = "SYNTHETIC RAW TRANSCRIPT PHRASE"
    _write_config(
        config,
        f"""
providers:
  - provider_name: FixtureProvider
    enabled: true
    api_key_env_var: FIXTURE_API_KEY
    base_url: https://api.example.com/transcripts
    license_config_ref: license://fixture
    allow_raw_storage: false
    allow_eval_use: false
    allow_training_use: false
    candidate_cases:
      - case_id: jpm_2025_q1
        ticker: JPM
        company_name: JPMorgan Chase & Co.
        fiscal_period: FY2025 Q1
        event_date: "2025-04-14"
        synthetic_raw_text: {raw_phrase}
""",
    )

    summary = run_discovery(config_path=config, out_csv=out_csv, report_path=report)

    assert summary["candidates_written"] == 1
    with out_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["rights_status"] == "licensed_vendor_metadata_only"
    assert raw_phrase not in out_csv.read_text(encoding="utf-8")
    assert raw_phrase not in report.read_text(encoding="utf-8")
