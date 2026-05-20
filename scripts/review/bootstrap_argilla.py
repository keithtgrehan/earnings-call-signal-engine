#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from review.suggestions import SIGNALS  # noqa: E402
from review.storage import INSTALL_GUIDANCE  # noqa: E402


def _require_argilla():
    try:
        import argilla as rg  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Argilla is required for review bootstrap. {INSTALL_GUIDANCE}") from exc
    return rg


def _is_local_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"}


def main() -> int:
    api_url = os.environ.get("ARGILLA_API_URL", "http://localhost:6900")
    api_key = os.environ.get("ARGILLA_API_KEY", "argilla.apikey")
    workspace_name = os.environ.get("ARGILLA_WORKSPACE", "signal-engine")
    dataset_name = os.environ.get("ARGILLA_DATASET", "earnings-call-review")
    allow_remote = os.environ.get("ARGILLA_ALLOW_REMOTE", "").lower() in {"1", "true", "yes"}
    if not _is_local_url(api_url) and not allow_remote:
        raise SystemExit("Refusing non-local Argilla URL. Set ARGILLA_ALLOW_REMOTE=true only for an explicitly approved private deployment.")

    rg = _require_argilla()
    client = rg.Argilla(api_url=api_url, api_key=api_key)
    try:
        workspaces = client.workspaces
        workspace = workspaces(workspace_name) if callable(workspaces) else None
    except Exception as exc:  # pragma: no cover - depends on Argilla server version
        raise SystemExit(f"Could not connect to Argilla at {api_url}: {exc}") from exc

    if workspace is None:
        workspace = rg.Workspace(name=workspace_name)
        workspace.create()
        print(f"created workspace: {workspace_name}")
    else:
        print(f"workspace exists: {workspace_name}")

    settings = rg.Settings(
        fields=[rg.TextField(name="text", title="Transcript chunk", required=True)],
        questions=[
            rg.MultiLabelQuestion(
                name="signals",
                title="Human-reviewed signal labels",
                labels=SIGNALS,
                required=False,
            )
        ],
        metadata=[
            rg.TermsMetadataProperty(name="case_id"),
            rg.TermsMetadataProperty(name="chunk_id"),
            rg.TermsMetadataProperty(name="section"),
            rg.TermsMetadataProperty(name="speaker"),
            rg.TermsMetadataProperty(name="review_state"),
        ],
    )
    dataset = client.datasets(name=dataset_name, workspace=workspace_name)
    if dataset is None:
        dataset = rg.Dataset(name=dataset_name, workspace=workspace_name, settings=settings)
        dataset.create()
        print(f"created dataset: {dataset_name}")
    else:
        print(f"dataset exists: {dataset_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
