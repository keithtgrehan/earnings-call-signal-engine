#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.gold_review import audit_gold_labels, write_gold_audit_outputs
from signal_engine.artifacts.manifest import build_artifact_manifest, write_artifact_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit canonical gold labels without modifying them.")
    parser.add_argument("--path", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--out-dir", default="reports/gold_label_audit")
    args = parser.parse_args(argv)
    summary = audit_gold_labels(Path(args.path))
    out_dir = Path(args.out_dir)
    write_gold_audit_outputs(summary, out_dir)
    write_artifact_manifest(
        out_dir / "artifact_manifest.json",
        build_artifact_manifest(
            run_id="gold_audit",
            command="python scripts/audit_gold_labels.py",
            inputs=[Path(args.path)],
            outputs=[out_dir / "gold_label_audit.json", out_dir / "gold_label_audit.md"],
            schema_versions={"gold_audit": "1.0.0"},
            generated_by="scripts/audit_gold_labels.py",
            deterministic_core_version="gold_review_v1",
        ),
    )
    print(f"Gold-label audit complete: {summary['valid_count']} valid row(s), canonical gold file unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
