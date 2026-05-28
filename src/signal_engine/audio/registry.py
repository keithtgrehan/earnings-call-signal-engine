from __future__ import annotations

from pathlib import Path


def validate_audio_registry_row(row: dict[str, str], *, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if row.get("asset_type") != "audio":
        errors.append("asset_type must be audio")
    if row.get("commit_allowed") != "false":
        errors.append("commit_allowed must be false")
    if row.get("training_allowed") != "false":
        errors.append("training_allowed must be false")
    if row.get("eval_allowed") == "true" and not row.get("approval_ref"):
        errors.append("eval_allowed=true requires approval_ref")
    local_path = Path(row.get("local_path", ""))
    if repo_root and str(local_path) not in {"", "."}:
        try:
            local_path.resolve().relative_to(repo_root.resolve())
            errors.append("raw audio path must not be inside git repo")
        except (OSError, ValueError):
            pass
    return errors
