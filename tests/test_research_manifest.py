from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_research_manifest.py"


def test_multimodal_research_manifest_builds_expected_outputs(tmp_path: Path) -> None:
    json_out = tmp_path / "research_manifest.json"
    markdown_out = tmp_path / "dataset_and_research_map.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    markdown = markdown_out.read_text(encoding="utf-8")

    assert payload["entry_count"] >= 28
    assert len(payload["entries"]) == payload["entry_count"]
    modalities = {entry["modality"] for entry in payload["entries"]}
    assert {"transcript", "audio", "video", "multimodal"} <= modalities
    assert "Dataset and Research Map" in markdown

    first = payload["entries"][0]
    assert {
        "id",
        "title",
        "url",
        "type",
        "modality",
        "relevance_to_signal_engine",
        "possible_labels_or_features",
        "access_status",
        "license_notes",
        "download_status",
        "recommended_use",
        "limitations",
    } <= set(first)
