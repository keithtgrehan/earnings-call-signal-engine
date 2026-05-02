#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_run(gold: Path, config: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot = output_dir / "gold_labels.snapshot.jsonl"
    if gold.exists():
        shutil.copyfile(gold, snapshot)
    payload = {
        "status": "packaged" if gold.exists() else "no_gold_labels_available",
        "dataset_snapshot": str(snapshot) if gold.exists() else None,
        "dataset_sha256": sha256(snapshot) if gold.exists() else None,
        "training_config": str(config),
        "do_not_run_conditions": [
            "gold_labels < 500 for full train/dev/test",
            "no saved splits",
            "no MLflow tracking destination",
            "unreviewed weak labels only",
            "unaligned audio/video media",
        ],
    }
    (output_dir / "training_run_manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a remote training run manifest without executing remote compute.")
    parser.add_argument("--gold", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--config", default=str(ROOT / "configs" / "training" / "remote_gpu_plan.yaml"))
    parser.add_argument("--out-dir", default=str(ROOT / "data" / "training_runs" / "latest"))
    args = parser.parse_args()
    payload = package_run(Path(args.gold), Path(args.config), Path(args.out_dir))
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
