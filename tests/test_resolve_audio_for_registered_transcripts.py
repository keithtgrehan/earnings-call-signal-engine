from __future__ import annotations

from pathlib import Path

from tools.first30_transcript_common import write_csv
from tools.resolve_audio_for_registered_transcripts import resolve_audio_for_registered_transcripts
from tools.resolve_first30_audio_candidates import AUDIO_FIELDS


TRANSCRIPT_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "local_path",
    "sha256",
    "source_url",
    "provenance_path",
    "rights_status",
    "eval_allowed",
    "commit_allowed",
    "training_allowed",
    "approval_ref",
    "registered_timestamp",
    "notes",
]

GAP_FIELDS = ["case_id", "ticker", "source_type", "source_relation", "notes"]


def test_audio_coverage_preserves_webcast_player_metadata_only(tmp_path: Path) -> None:
    transcripts = tmp_path / "transcripts.csv"
    ingestion = tmp_path / "ingestion.csv"
    audio = tmp_path / "audio.csv"
    gaps = tmp_path / "gaps.csv"
    out = tmp_path / "audio_candidates.csv"
    audit = tmp_path / "_audit"
    write_csv(
        transcripts,
        [
            {
                "case_id": "hd_2025_q4",
                "ticker": "HD",
                "company_name": "The Home Depot Inc.",
                "asset_type": "transcript",
                "local_path": "/tmp/nonraw.txt",
                "sha256": "sha256:x",
                "source_url": "https://ir.homedepot.com/example.pdf",
                "provenance_path": "",
                "rights_status": "safe_to_download",
                "eval_allowed": "true",
                "commit_allowed": "false",
                "training_allowed": "false",
                "approval_ref": "user_authorized_project_assessment",
                "registered_timestamp": "",
                "notes": "",
            }
        ],
        TRANSCRIPT_FIELDS,
    )
    write_csv(gaps, [{"case_id": "hd_2025_q4", "ticker": "HD", "source_type": "webcast_player_only", "source_relation": "metadata_only", "notes": ""}], GAP_FIELDS)

    summary = resolve_audio_for_registered_transcripts(
        transcript_registry=transcripts,
        ingestion_manifest=ingestion,
        audio_registry=audio,
        source_gap_manifest=gaps,
        out_path=out,
        audit_dir=audit,
    )

    assert summary["direct_audio_download_allowed"] == 0
    assert summary["webcast_metadata_only"] == 1
    assert out.exists()
    assert (audit / "first30_audio_candidates.csv").exists()


def test_audio_candidate_fields_remain_guarded() -> None:
    assert "commit_allowed" in AUDIO_FIELDS
    assert "training_allowed" in AUDIO_FIELDS
    assert "raw_audio_committed" in AUDIO_FIELDS
