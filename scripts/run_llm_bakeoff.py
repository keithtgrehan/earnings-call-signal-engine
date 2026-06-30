#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_llm_fixture_smoke import _allowed_output_path, run_smoke
from signal_engine.llm import load_llm_config


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run fixed-fixture LLM provider bakeoff. Live providers skip by default.")
    parser.add_argument("--providers", default="dry_run")
    parser.add_argument("--task", choices=["signal_candidates", "evidence_judge"], default="signal_candidates")
    parser.add_argument("--fixture", default="tests/fixtures/tiny_realistic_earnings_excerpt.txt")
    parser.add_argument("--config", default="configs/llm.example.yml")
    parser.add_argument("--report-out", default="reports/llm/bakeoff_summary.json")
    parser.add_argument("--outputs-out", default="artifacts/llm/bakeoff_outputs.jsonl")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)

    config = load_llm_config(args.config)
    report_out = _allowed_output_path(Path(args.report_out), config.allowed_output_roots)
    outputs_out = _allowed_output_path(Path(args.outputs_out), config.allowed_output_roots)
    providers = [provider.strip() for provider in args.providers.split(",") if provider.strip()]
    rows: list[dict[str, Any]] = []
    exit_code = 0

    for provider in providers:
        provider_out = Path("artifacts") / "llm" / f"bakeoff_{provider}_{args.task}.json"
        code, artifact = run_smoke(
            provider_name=provider,
            task=args.task,
            fixture=(ROOT / args.fixture).resolve() if not Path(args.fixture).is_absolute() else Path(args.fixture).resolve(),
            out=provider_out,
            config_path=Path(args.config),
            live=args.live,
        )
        rows.append(artifact)
        if code != 0:
            exit_code = code

    summary = {
        "schema_version": "llm_bakeoff_summary.v1",
        "status": "valid" if exit_code == 0 else "invalid",
        "task": args.task,
        "providers": providers,
        "canonical_output": False,
        "provider_calls_performed": any(row.get("provider_calls_performed") for row in rows),
        "results": [
            {
                "provider": row["provider"],
                "status": row["status"],
                "validation_status": row["validation_status"],
                "provider_calls_performed": row["provider_calls_performed"],
            }
            for row in rows
        ],
    }
    _write_json(report_out, summary)
    _write_jsonl(outputs_out, rows)
    print(f"LLM bakeoff {summary['status']}: providers={','.join(providers)} calls={summary['provider_calls_performed']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
