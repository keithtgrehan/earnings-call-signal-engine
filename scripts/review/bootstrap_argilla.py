#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.review_schema import ALLOWED_REVIEW_ACTIONS, CANONICAL_REVIEW_FIELDS  # noqa: E402

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
INSTALL_HINT = 'Install local review extras with: pip install -e ".[review]"'


def is_local_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and (parsed.hostname or "") in LOCAL_HOSTS


def load_argilla() -> object:
    try:
        import argilla as rg  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise SystemExit(f"argilla is not installed. {INSTALL_HINT}") from exc
    return rg


def env_config() -> dict[str, str]:
    api_url = os.environ.get("ARGILLA_API_URL", "http://localhost:6900").strip()
    if not is_local_url(api_url) and os.environ.get("ARGILLA_ALLOW_NONLOCAL", "").lower() != "true":
        raise SystemExit("ARGILLA_API_URL must point to localhost by default. Set ARGILLA_ALLOW_NONLOCAL=true only for an explicitly reviewed local tunnel.")
    return {
        "api_url": api_url,
        "api_key": os.environ.get("ARGILLA_API_KEY", "").strip(),
        "workspace": os.environ.get("ARGILLA_WORKSPACE", "default").strip() or "default",
        "dataset": os.environ.get("ARGILLA_DATASET", "signal_engine_review").strip() or "signal_engine_review",
    }


def build_settings(rg: object) -> object:
    fields = [rg.TextField(name=field, title=field) for field in CANONICAL_REVIEW_FIELDS]
    questions = [
        rg.LabelQuestion(name="reviewer_action", title="reviewer_action", labels=sorted(ALLOWED_REVIEW_ACTIONS), required=True),
        rg.TextQuestion(name="reviewer_notes", title="reviewer_notes", required=False),
    ]
    return rg.Settings(fields=fields, questions=questions)


def dataset_exists(client: object, name: str, workspace: str) -> bool:
    try:
        client.datasets(name=name, workspace=workspace)
    except Exception:
        return False
    return True


def bootstrap(config: dict[str, str]) -> dict[str, str]:
    if not config["api_key"]:
        raise SystemExit("ARGILLA_API_KEY is required. Start Argilla locally, log in, and use a local API key.")
    rg = load_argilla()
    try:
        client = rg.Argilla(api_url=config["api_url"], api_key=config["api_key"])
        client.workspaces(config["workspace"])
    except Exception as exc:
        raise SystemExit(f"Could not connect to local Argilla workspace `{config['workspace']}` at {config['api_url']}: {exc}") from exc
    if dataset_exists(client, config["dataset"], config["workspace"]):
        return {"status": "exists", **config}
    try:
        dataset = rg.Dataset(name=config["dataset"], workspace=config["workspace"], settings=build_settings(rg))
        dataset.create()
    except Exception as exc:
        raise SystemExit(f"Could not create Argilla dataset `{config['dataset']}` in workspace `{config['workspace']}`: {exc}") from exc
    return {"status": "created", **config}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the local Argilla dataset for Signal Engine review.")
    parser.add_argument("--check-only", action="store_true", help="Validate configuration and dependency without creating a dataset.")
    args = parser.parse_args(argv)
    config = env_config()
    if args.check_only:
        load_argilla()
        print({"status": "config_ok", **config})
        return 0
    print(bootstrap(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
