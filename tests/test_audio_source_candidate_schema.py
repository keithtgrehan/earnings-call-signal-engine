from __future__ import annotations

import json
from pathlib import Path


def test_audio_source_candidate_defaults_fail_closed_fields_required() -> None:
    schema = json.loads(Path("schemas/audio_source_candidate.schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])

    assert {"rights_status", "download_allowed", "approval_required"}.issubset(required)
    assert schema["properties"]["commit_allowed"]["const"] is False
    assert schema["properties"]["training_allowed"]["const"] is False
