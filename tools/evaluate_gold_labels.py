#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import read_jsonl  # noqa: E402
from signal_engine.evaluation_backbone import model_metrics  # noqa: E402
from signal_engine.signal_baseline import predict_deterministic_signal_family  # noqa: E402


def gate_for_count(count: int) -> tuple[str, bool]:
    if count < 20:
        return "insufficient_data", False
    if count < 100:
        return "preliminary_metrics_only", True
    if count < 500:
        return "early_benchmark", True
    return "train_dev_test_split_allowed", True


def write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Benchmark Status",
        "",
        f"- gold_labels: `{payload['gold_labels']}`",
        f"- gate: `{payload['gate']}`",
        f"- metrics_computed: `{payload['metrics_computed']}`",
        "",
    ]
    if payload.get("metrics"):
        lines.extend(["## Metrics", "", "```json", json.dumps(payload["metrics"], indent=2), "```"])
    else:
        lines.append("Insufficient data: metrics are intentionally not computed below 20 gold labels.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluate(rows: list[dict[str, object]]) -> dict[str, object]:
    gate, metrics_allowed = gate_for_count(len(rows))
    payload: dict[str, object] = {"gold_labels": len(rows), "gate": gate, "metrics_computed": False, "metrics": None}
    if not metrics_allowed:
        return payload
    y_true: list[str] = []
    y_pred: list[str] = []
    for row in rows:
        text = str(row.get("text") or "")
        label = str(row.get("signal_family") or row.get("label") or "")
        if not text or not label:
            continue
        y_true.append(label)
        y_pred.append(str(predict_deterministic_signal_family(text).get("label")))
    payload["metrics_computed"] = bool(y_true)
    payload["metrics"] = model_metrics(y_true, y_pred) if y_true else None
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic baseline against gold labels with strict gates.")
    parser.add_argument("--gold", default=str(ROOT / "data" / "gold" / "gold_labels.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "docs" / "evaluation" / "benchmark_status.md"))
    args = parser.parse_args(argv)
    rows = read_jsonl(Path(args.gold))
    payload = evaluate(rows)
    write_report(Path(args.out), payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
