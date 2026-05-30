from __future__ import annotations

from pathlib import Path


def test_retrieval_manifests_do_not_expose_raw_text_column() -> None:
    header = Path("data/retrieval/retrieval_objects_manifest.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "evidence_text" not in header
    assert "raw_text_committed" in header
