from __future__ import annotations

from pathlib import Path

from signal_engine.chunking.validate_chunks import validate_chunk_manifest_rows


def test_chunk_validation_rejects_repo_chunk_paths(tmp_path: Path) -> None:
    row = {
        "chunk_id": "chunk1",
        "chunk_type": "qa_pair",
        "source_sha256": "sha256:" + "a" * 64,
        "text_sha256": "sha256:" + "b" * 64,
        "raw_text_committed": "false",
        "local_chunk_path": str(tmp_path / "chunk.txt"),
    }

    errors = validate_chunk_manifest_rows([row], repo_root=tmp_path)

    assert any("local_chunk_path" in error for error in errors)


def test_chunk_validation_accepts_repo_safe_metadata() -> None:
    row = {
        "chunk_id": "chunk1",
        "chunk_type": "qa_pair",
        "source_sha256": "sha256:" + "a" * 64,
        "text_sha256": "sha256:" + "b" * 64,
        "raw_text_committed": "false",
        "local_chunk_path": "/tmp/desktop/chunk.txt",
    }

    assert validate_chunk_manifest_rows([row], repo_root=Path("/repo")) == []
