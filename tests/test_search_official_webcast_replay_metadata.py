from __future__ import annotations

from pathlib import Path

from tools.first30_transcript_common import read_csv, write_csv
import tools.search_official_webcast_replay_metadata as webcast


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


def test_event_match_derives_period_from_case_id() -> None:
    row = {"case_id": "f_2025_q4", "ticker": "F"}
    event = {"Title": "Ford 4Q25 Earnings Conference Call", "TagsList": []}

    assert webcast._event_matches_case(event, row)


def test_webcast_metadata_writes_metadata_only_rows(tmp_path: Path, monkeypatch) -> None:
    registry = tmp_path / "manual_local_transcript_registry.csv"
    out = tmp_path / "first30_webcast_replay_metadata.csv"
    audit = tmp_path / "_audit"
    write_csv(
        registry,
        [
            {
                "case_id": "f_2025_q4",
                "ticker": "F",
                "company_name": "Ford Motor Company",
                "asset_type": "transcript",
                "local_path": "/tmp/nonraw.txt",
                "sha256": "sha256:x",
                "source_url": "https://shareholder.ford.com/example.pdf",
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
    monkeypatch.setattr(
        webcast,
        "_events",
        lambda host: [{"Title": "Ford 4Q25 Earnings Conference Call", "TagsList": [], "WebCastLink": "https://shareholder.ford.com/events/player"}],
    )

    summary = webcast.search_official_webcast_replay_metadata(
        transcript_registry=registry,
        out_path=out,
        audit_dir=audit,
    )

    rows = read_csv(out)
    assert summary["webcast_player_only"] == 1
    assert rows[0]["download_allowed"] == "false"
    assert rows[0]["metadata_only"] == "true"
    assert (audit / "first30_webcast_replay_metadata.csv").exists()
