#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from review.chunking import read_jsonl  # noqa: E402
from review.suggestions import SIGNALS, suggestions_by_chunk  # noqa: E402


def evaluate(gold_rows: list[dict[str, object]], suggestion_rows: list[dict[str, object]], *, min_labels: int = 5) -> dict[str, object]:
    reviewed = len(gold_rows)
    payload: dict[str, object] = {
        "reviewed_labels": reviewed,
        "metrics_computed": False,
        "caveat": "",
        "per_signal": {},
        "micro": {},
        "acceptance_rates": {},
    }
    if reviewed < min_labels:
        payload["caveat"] = f"Only {reviewed} reviewed rows available; metrics skipped below min_labels={min_labels}."
        return payload
    grouped = suggestions_by_chunk(suggestion_rows)
    totals: dict[str, Counter[str]] = {label: Counter() for label in SIGNALS}
    for row in gold_rows:
        chunk_id = str(row.get("chunk_id") or "")
        truth = set(str(label) for label in (row.get("labels") or []) if label in SIGNALS)
        predicted = set(str(s.get("label")) for s in grouped.get(chunk_id, []) if s.get("label") in SIGNALS)
        for label in SIGNALS:
            if label in truth and label in predicted:
                totals[label]["tp"] += 1
            elif label not in truth and label in predicted:
                totals[label]["fp"] += 1
            elif label in truth and label not in predicted:
                totals[label]["fn"] += 1
            else:
                totals[label]["tn"] += 1
    micro = Counter()
    per_signal: dict[str, dict[str, float | int]] = {}
    for label, counts in totals.items():
        micro.update({"tp": counts["tp"], "fp": counts["fp"], "fn": counts["fn"]})
        per_signal[label] = _metrics(counts)
    payload["metrics_computed"] = True
    payload["per_signal"] = per_signal
    payload["micro"] = _metrics(micro)
    payload["caveat"] = "Early reviewed-label metrics only; do not treat as statistically meaningful."
    return payload


def _metrics(counts: Counter[str]) -> dict[str, float | int]:
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def write_outputs(out_dir: Path, payload: dict[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "review_metrics.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (out_dir / "per_signal_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["signal", "tp", "fp", "fn", "precision", "recall", "f1"])
        writer.writeheader()
        for signal, metrics in sorted(dict(payload.get("per_signal") or {}).items()):
            writer.writerow({"signal": signal, **metrics})
    lines = ["# Review Evaluation", "", f"- reviewed_labels: `{payload['reviewed_labels']}`", f"- metrics_computed: `{payload['metrics_computed']}`", ""]
    if payload.get("caveat"):
        lines.extend(["## Caveat", "", str(payload["caveat"]), ""])
    if payload.get("micro"):
        lines.extend(["## Micro Metrics", "", "```json", json.dumps(payload["micro"], indent=2), "```", ""])
    (out_dir / "review_evaluation.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate weak-label suggestions against explicit human-reviewed gold rows.")
    parser.add_argument("--gold", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "gold_labels.review_export.jsonl"))
    parser.add_argument("--suggestions", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "argilla_suggestions.jsonl"))
    parser.add_argument("--out-dir", default=str(ROOT / "reports" / "review_eval"))
    parser.add_argument("--min-labels", type=int, default=5)
    args = parser.parse_args(argv)
    payload = evaluate(read_jsonl(Path(args.gold)), read_jsonl(Path(args.suggestions)), min_labels=args.min_labels)
    write_outputs(Path(args.out_dir), payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
