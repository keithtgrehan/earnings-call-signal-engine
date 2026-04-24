#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _run_json_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _run_command(
    command: list[str],
    *,
    check: bool = True,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _extract_key_signals(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_flags": payload.get("risk_flags", []),
        "opportunity_flags": payload.get("opportunity_flags", []),
        "top_evidence": payload.get("evidence", [])[:3],
        "redaction_summary": payload.get("metadata", {}).get("pii_redaction"),
    }


def _transformer_runtime_available() -> bool:
    return (
        importlib.util.find_spec("transformers") is not None
        and importlib.util.find_spec("torch") is not None
    )


def run_demo(*, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    benchmark_dir = out_dir / "text_emotion_benchmark"

    commands_run: list[str] = []

    support_command = [
        sys.executable,
        "scripts/signal_engine_analyze.py",
        "--domain",
        "support",
        "data/signal_engine_2_0/sample_support.json",
    ]
    commands_run.append(" ".join(support_command))
    support_payload = _run_json_command(support_command)
    _write_json(out_dir / "support_output.json", support_payload)

    sales_command = [
        sys.executable,
        "scripts/signal_engine_analyze.py",
        "--domain",
        "sales",
        "data/signal_engine_2_0/sample_sales.json",
    ]
    commands_run.append(" ".join(sales_command))
    sales_payload = _run_json_command(sales_command)
    _write_json(out_dir / "sales_output.json", sales_payload)

    account_command = [
        sys.executable,
        "scripts/signal_engine_analyze.py",
        "--domain",
        "account_management",
        "data/signal_engine_2_0/sample_account_management.json",
    ]
    commands_run.append(" ".join(account_command))
    account_payload = _run_json_command(account_command)
    _write_json(out_dir / "account_management_output.json", account_payload)

    pii_command = [
        sys.executable,
        "scripts/signal_engine_analyze.py",
        "--domain",
        "support",
        "--redact-pii",
        "data/signal_engine_2_0/fixtures/support_tickets_realistic.jsonl",
    ]
    commands_run.append(" ".join(pii_command))
    pii_payload = _run_json_command(pii_command)
    _write_json(out_dir / "pii_redacted_support_output.json", pii_payload)

    benchmark_command = [
        sys.executable,
        "scripts/run_text_emotion_benchmark.py",
        "--input",
        "data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl",
        "--manifest",
        "data/signal_engine_2_0/dataset_manifests/emotion_benchmark_manifest.json",
        "--mode",
        "deterministic",
        "--redact-pii",
        "--out-dir",
        str(benchmark_dir),
    ]
    commands_run.append(" ".join(benchmark_command))
    benchmark_status = _run_json_command(benchmark_command)
    benchmark_metrics = json.loads((benchmark_dir / "metrics.json").read_text(encoding="utf-8"))

    transformer_status = "Optional transformer benchmark not run because dependency/model cache unavailable."
    if _transformer_runtime_available():
        transformer_dir = ROOT / "outputs" / "signal_engine_2_0" / "text_emotion_transformer_optional"
        transformer_command = [
            sys.executable,
            "scripts/run_text_emotion_benchmark.py",
            "--input",
            "data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl",
            "--manifest",
            "data/signal_engine_2_0/dataset_manifests/emotion_benchmark_manifest.json",
            "--mode",
            "transformers",
            "--model-id",
            "j-hartmann/emotion-english-distilroberta-base",
            "--out-dir",
            str(transformer_dir),
        ]
        commands_run.append(" ".join(transformer_command))
        try:
            completed = _run_command(
                transformer_command,
                check=False,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            transformer_status = (
                "Optional transformer benchmark not run because dependency/model cache availability "
                "could not be confirmed quickly without risking a slow demo pass."
            )
        else:
            if completed.returncode == 0:
                transformer_status = (
                    "Optional transformer benchmark ran successfully at "
                    f"{transformer_dir}."
                )
            else:
                stderr = completed.stderr.strip() or completed.stdout.strip()
                transformer_status = (
                    "Optional transformer benchmark not run because dependency/model cache unavailable. "
                    f"Runner output: {stderr}"
                )

    demo_index = f"""# Signal Engine 2.0 Final Demo Index

## Commands Run

""" + "\n".join(f"- `{command}`" for command in commands_run) + f"""

## Key Signals By Domain

- support: `{", ".join(support_payload["risk_flags"] + support_payload["opportunity_flags"])}`  
- sales: `{", ".join(sales_payload["risk_flags"] + sales_payload["opportunity_flags"])}`  
- account management: `{", ".join(account_payload["risk_flags"] + account_payload["opportunity_flags"])}`  

## PII Redaction

- enabled: `true`
- redaction summary: `{json.dumps(pii_payload["metadata"].get("pii_redaction", {}), sort_keys=True)}`

## Text Emotion Benchmark

- macro F1: `{benchmark_metrics["macro_f1"]}`
- redactions enabled: `{str(benchmark_status["redactions_enabled"]).lower()}`
- warning: tiny handcrafted fixture, useful for harness validation only

## Optional Transformer Status

- {transformer_status}

## Known Limitations

- deterministic transcript outputs remain canonical
- benchmark fixture is tiny and handcrafted
- audio/video/retrieval remain adapter-ready roadmap
- no truth-detection or black-box emotion score is treated as product truth
"""
    (out_dir / "demo_index.md").write_text(demo_index + "\n", encoding="utf-8")

    return {
        "support": _extract_key_signals(support_payload),
        "sales": _extract_key_signals(sales_payload),
        "account_management": _extract_key_signals(account_payload),
        "pii_redacted_support": _extract_key_signals(pii_payload),
        "benchmark_metrics": benchmark_metrics,
        "transformer_status": transformer_status,
        "commands_run": commands_run,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the final Signal Engine 2.0 demo package."
    )
    parser.add_argument(
        "--out-dir",
        default="outputs/signal_engine_2_0/final_demo",
        help="Directory for final demo artifacts.",
    )
    args = parser.parse_args(argv)

    result = run_demo(out_dir=Path(args.out_dir))
    print(
        json.dumps(
            {
                "status": "ok",
                "out_dir": str(Path(args.out_dir).resolve()),
                "benchmark_macro_f1": result["benchmark_metrics"]["macro_f1"],
                "transformer_status": result["transformer_status"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
