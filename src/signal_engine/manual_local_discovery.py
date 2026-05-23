from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import os
import re
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _infer_case_id(path: Path) -> str:
    stem = path.stem.lower()
    match = re.search(r"([a-z]{1,6}).*?(20\d{2}).*?(q[1-4])", stem)
    if match:
        return f"{match.group(1)}_{match.group(2)}_{match.group(3)}"
    return stem


def discover_manual_local_paths(
    *,
    search_dirs: Iterable[Path],
    approved_dirs: Iterable[Path],
    allowed_extensions: set[str],
    source_kind: str,
    max_depth: int = 4,
    max_files: int = 500,
) -> list[dict[str, object]]:
    approved = [Path(path).expanduser() for path in approved_dirs]
    rows: list[dict[str, object]] = []
    now = datetime.now(UTC).isoformat()
    for search_dir in search_dirs:
        root = Path(search_dir).expanduser()
        if not root.exists():
            continue
        for path in _iter_files(root, max_depth=max_depth, max_files=max_files):
            if path.suffix.lower() not in allowed_extensions:
                continue
            in_approved = any(_is_relative_to(path, approved_dir) for approved_dir in approved)
            status = "candidate_metadata_only" if in_approved else "blocked_outside_approved_directories"
            rows.append(
                {
                    "path_ref": str(path),
                    "source_kind": source_kind,
                    "status": status,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "modified_time": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
                    "candidate_case_id": _infer_case_id(path),
                    "rights_status": "unknown",
                    "blocked_reason_code": "source_rights_unknown" if in_approved else "outside_approved_directories",
                    "raw_file_copied_into_repo": False,
                    "body_parsed": False,
                    "ocr_run": False,
                    "asr_run": False,
                    "video_processed": False,
                    "discovered_at": now,
                }
            )
    return rows


def _iter_files(root: Path, *, max_depth: int, max_files: int) -> list[Path]:
    files: list[Path] = []
    root = root.resolve()
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        rel_parts = current_path.relative_to(root).parts
        if len(rel_parts) >= max_depth:
            dirs[:] = []
        dirs[:] = [name for name in dirs if not name.startswith(".") and name not in {"node_modules", ".git", "__pycache__"}]
        for name in names:
            files.append(current_path / name)
            if len(files) >= max_files:
                return sorted(files)
    return sorted(files)
