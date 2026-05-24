from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.acquire_nyse_100_assets as acquire_module


MANIFEST_FIELDS = [
    "case_id",
    "ticker_symbol",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "calendar_year",
    "earnings_call_date",
    "transcript_source_url",
    "audio_source_url",
    "video_source_url",
    "transcript_availability",
    "audio_availability",
    "video_availability",
    "source_type",
    "rights_status",
    "priority_tier",
    "local_paths_created",
    "notes",
    "source_domain",
    "discovered_timestamp",
    "acquisition_method",
    "provenance_hash",
    "call_folder",
]

REGISTRY_FIELDS = [
    "registry_id",
    "case_id",
    "ticker_symbol",
    "company_name",
    "fiscal_year",
    "fiscal_quarter",
    "source_type",
    "asset_type",
    "source_url",
    "source_domain",
    "availability",
    "rights_status",
    "raw_download_allowed",
    "blocked_reason",
    "manual_action",
    "license_config_ref",
    "allow_eval_use",
    "allow_training_use",
    "acquisition_method",
    "discovered_timestamp",
    "provenance_hash",
    "notes",
]


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _manifest_row(tmp_path: Path, **overrides: str) -> dict[str, str]:
    row = {
        "case_id": "jpm_2025_q1",
        "ticker_symbol": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "exchange": "NYSE",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "calendar_year": "2025",
        "earnings_call_date": "2025-04-14",
        "transcript_source_url": "https://ir.example.com/transcript",
        "audio_source_url": "https://ir.example.com/audio.mp3",
        "video_source_url": "",
        "transcript_availability": "unknown",
        "audio_availability": "unknown",
        "video_availability": "unknown",
        "source_type": "company_ir",
        "rights_status": "metadata_only",
        "priority_tier": "4",
        "local_paths_created": "false",
        "notes": "Synthetic test row.",
        "source_domain": "ir.example.com",
        "discovered_timestamp": "2026-05-24T00:00:00+00:00",
        "acquisition_method": "test",
        "provenance_hash": "sha256:" + "a" * 64,
        "call_folder": str(tmp_path / "unused"),
    }
    row.update(overrides)
    return row


def _registry_row(**overrides: str) -> dict[str, str]:
    row = {
        "registry_id": "jpm_2025_q1_company_ir_1",
        "case_id": "jpm_2025_q1",
        "ticker_symbol": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "source_type": "company_ir",
        "asset_type": "transcript",
        "source_url": "https://ir.example.com/transcript",
        "source_domain": "ir.example.com",
        "availability": "unknown",
        "rights_status": "metadata_only",
        "raw_download_allowed": "false",
        "blocked_reason": "",
        "manual_action": "Review rights.",
        "license_config_ref": "",
        "allow_eval_use": "false",
        "allow_training_use": "false",
        "acquisition_method": "test",
        "discovered_timestamp": "2026-05-24T00:00:00+00:00",
        "provenance_hash": "sha256:" + "b" * 64,
        "notes": "Synthetic source.",
    }
    row.update(overrides)
    return row


def _write_policy(path: Path, *, allow_transcripts: bool = False, allow_audio: bool = False) -> None:
    path.write_text(
        "\n".join(
            [
                "enabled: true",
                "metadata_only_default: true",
                f"allow_transcript_downloads: {str(allow_transcripts).lower()}",
                f"allow_audio_downloads: {str(allow_audio).lower()}",
                "allow_youtube_downloads: false",
                "allow_vendor_downloads: false",
                "require_rights_status_safe_to_download: true",
                "require_source_url: true",
                "require_provenance: true",
                "max_requests_per_second: 100",
                'user_agent: "SignalEngine test"',
                "allowed_source_types_for_transcript_download:",
                "  - company_ir",
                "  - official_ir_transcript",
                "  - sec_edgar_allowed_exhibit",
                "  - manually_approved_source",
                "allowed_source_types_for_audio_download:",
                "  - company_ir",
                "  - official_ir_webcast",
                "  - manually_approved_source",
                "blocked_source_types:",
                "  - youtube_metadata_only",
                "  - licensed_vendor_blocked",
                "  - restricted_source_blocked",
                "  - paywalled",
                "  - login_required",
                "raw_git_commit_allowed: false",
                "chunking_enabled: true",
                "asr_enabled: false",
                "asr_provider: none",
                "rag_index_mode: manifest_only",
                "vector_db_enabled: false",
                "embeddings_enabled: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_manual_approvals(path: Path) -> None:
    path.write_text("approvals: []\n", encoding="utf-8")


def _run_acquire(
    tmp_path: Path,
    manifest_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
    monkeypatch,
    *,
    allow_transcripts: bool = False,
    allow_audio: bool = False,
) -> tuple[Path, list[dict[str, str]]]:
    manifest = tmp_path / "manifest.csv"
    registry = tmp_path / "registry.csv"
    policy = tmp_path / "policy.yml"
    approvals = tmp_path / "approvals.yml"
    workspace = tmp_path / "desktop_workspace"
    _write_csv(manifest, manifest_rows, MANIFEST_FIELDS)
    _write_csv(registry, registry_rows, REGISTRY_FIELDS)
    _write_policy(policy, allow_transcripts=allow_transcripts, allow_audio=allow_audio)
    _write_manual_approvals(approvals)
    monkeypatch.setattr(acquire_module, "REPORT_DIR", tmp_path / "repo_reports")

    exit_code = acquire_module.main(
        [
            "--manifest",
            str(manifest),
            "--source-registry",
            str(registry),
            "--policy",
            str(policy),
            "--manual-approvals",
            str(approvals),
            "--workspace",
            str(workspace),
            "--target-count",
            "1",
            "--start-year",
            "2025",
            "--years-back",
            "5",
            "--run-mode",
            "permitted-only",
            "--max-workers",
            "1",
        ]
    )
    assert exit_code == 0
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    with audit.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return workspace, rows


def test_metadata_only_creates_folders_and_provenance(tmp_path: Path, monkeypatch) -> None:
    workspace, audit_rows = _run_acquire(tmp_path, [_manifest_row(tmp_path)], [_registry_row()], monkeypatch)

    call_folder = workspace / "JPM_JPMorgan_Chase_Co" / "2025-04-14_FY2025_Q1"
    assert (call_folder / "transcript").is_dir()
    assert (call_folder / "audio").is_dir()
    assert (call_folder / "video").is_dir()
    assert (call_folder / "metadata").is_dir()
    assert (call_folder / "provenance").is_dir()
    assert (call_folder / "chunks").is_dir()
    assert audit_rows[0]["download_status"] == "metadata_only"
    assert audit_rows[0]["provenance_hash"].startswith("sha256:")
    provenance_files = list((call_folder / "provenance").glob("*.json"))
    assert provenance_files
    assert json.loads(provenance_files[0].read_text(encoding="utf-8"))["raw_git_committed"] is False


def test_unknown_rights_blocks_downloads(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Prepared remarks", encoding="utf-8")

    workspace, audit_rows = _run_acquire(
        tmp_path,
        [_manifest_row(tmp_path, transcript_availability="available")],
        [
            _registry_row(
                source_url=source.as_uri(),
                availability="available",
                rights_status="unknown",
                raw_download_allowed="true",
            )
        ],
        monkeypatch,
        allow_transcripts=True,
    )

    assert audit_rows[0]["download_status"] == "blocked"
    assert "rights" in audit_rows[0]["blocked_reason"]
    assert not list(workspace.glob("**/*_transcript.txt"))


def test_youtube_audio_is_blocked_even_when_marked_safe(tmp_path: Path, monkeypatch) -> None:
    workspace, audit_rows = _run_acquire(
        tmp_path,
        [_manifest_row(tmp_path, audio_availability="available")],
        [
            _registry_row(
                registry_id="jpm_2025_q1_youtube_1",
                asset_type="audio",
                source_type="youtube_metadata_only",
                source_url="https://www.youtube.com/watch?v=abc123",
                source_domain="youtube.com",
                availability="available",
                rights_status="safe_to_download",
                raw_download_allowed="true",
            )
        ],
        monkeypatch,
        allow_audio=True,
    )

    assert audit_rows[0]["download_status"] == "blocked"
    assert "youtube" in audit_rows[0]["blocked_reason"].lower()
    assert not list(workspace.glob("**/*.mp3"))


def test_vendor_raw_is_blocked_without_license_config(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "vendor.txt"
    source.write_text("Vendor transcript", encoding="utf-8")

    _, audit_rows = _run_acquire(
        tmp_path,
        [_manifest_row(tmp_path, transcript_availability="available")],
        [
            _registry_row(
                registry_id="jpm_2025_q1_vendor_1",
                source_type="licensed_vendor_blocked",
                source_url=source.as_uri(),
                availability="available",
                rights_status="safe_to_download",
                raw_download_allowed="true",
            )
        ],
        monkeypatch,
        allow_transcripts=True,
    )

    assert audit_rows[0]["download_status"] == "blocked"
    assert "license" in audit_rows[0]["blocked_reason"].lower()


def test_safe_transcript_download_writes_txt_to_workspace_not_repo(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "allowed_transcript.txt"
    source.write_text("Operator: welcome to the earnings call.\n", encoding="utf-8")

    workspace, audit_rows = _run_acquire(
        tmp_path,
        [_manifest_row(tmp_path, transcript_availability="available", rights_status="safe_to_download")],
        [
            _registry_row(
                source_url=source.as_uri(),
                availability="available",
                rights_status="safe_to_download",
                raw_download_allowed="true",
            )
        ],
        monkeypatch,
        allow_transcripts=True,
    )

    downloaded = Path(audit_rows[0]["local_path"])
    assert audit_rows[0]["download_status"] == "downloaded"
    assert downloaded.exists()
    assert downloaded.suffix == ".txt"
    assert workspace in downloaded.parents
    assert ROOT not in downloaded.parents


def test_safe_audio_download_writes_audio_to_workspace_not_repo(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "allowed_audio.mp3"
    source.write_bytes(b"ID3synthetic-audio")

    workspace, audit_rows = _run_acquire(
        tmp_path,
        [_manifest_row(tmp_path, audio_availability="available", rights_status="safe_to_download")],
        [
            _registry_row(
                registry_id="jpm_2025_q1_audio_1",
                asset_type="audio",
                source_type="official_ir_webcast",
                source_url=source.as_uri(),
                source_domain="ir.example.com",
                availability="available",
                rights_status="safe_to_download",
                raw_download_allowed="true",
                allow_eval_use="true",
            )
        ],
        monkeypatch,
        allow_audio=True,
    )

    downloaded = Path(audit_rows[0]["local_path"])
    assert audit_rows[0]["download_status"] == "downloaded"
    assert downloaded.exists()
    assert downloaded.suffix == ".mp3"
    assert workspace in downloaded.parents
    assert ROOT not in downloaded.parents
