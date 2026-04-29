from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_signal_retrieval_index.py"
QUERY_SCRIPT = ROOT / "scripts" / "query_signal_retrieval_index.py"


def test_signal_retrieval_scaffold_builds_and_queries(tmp_path: Path) -> None:
    index_path = tmp_path / "signal_retrieval_index.json"
    status_path = tmp_path / "signal_retrieval_status.json"

    subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--index-out",
            str(index_path),
            "--status-out",
            str(status_path),
        ],
        cwd=ROOT,
        check=True,
    )
    query = subprocess.run(
        [
            sys.executable,
            str(QUERY_SCRIPT),
            "--index-path",
            str(index_path),
            "--query",
            "pricing objection and competitor pressure",
            "--top-k",
            "3",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    status_payload = json.loads(status_path.read_text(encoding="utf-8"))
    query_payload = json.loads(query.stdout)

    assert index_payload["status"] == "ok"
    assert status_payload["backend"] == "tfidf_cosine"
    assert query_payload["results"]
    assert len(query_payload["results"]) == 3
