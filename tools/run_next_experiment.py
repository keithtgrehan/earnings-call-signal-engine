#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from experiment_common import GOLD_PATH, gate_state, read_jsonl, row_label, valid_gold_rows  # noqa: E402

RESULT_DIR = ROOT / "reports" / "experiment_results"


def write_result(name: str, lines: list[str]) -> Path:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULT_DIR / f"{name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def deterministic_baseline(rows: list[dict[str, object]]) -> Path:
    lines = [
        "# Deterministic Baseline Experiment",
        "",
        f"- gold_labels: `{len(rows)}`",
        "- status: `completed_readiness_snapshot`",
        "",
        "Deterministic Signal Engine remains canonical. Metrics are produced only by the gated evaluation loop.",
    ]
    return write_result("deterministic_baseline", lines)


def local_ml_baseline(rows: list[dict[str, object]]) -> Path:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
    except Exception as exc:
        return write_result("local_ml_baseline", ["# Local ML Baseline", "", "- status: `skipped`", f"- reason: `{exc}`"])
    texts = [str(row.get("text") or row.get("evidence_text") or "") for row in rows]
    labels = [row_label(row) for row in rows]
    if len(set(labels)) < 2:
        return write_result("local_ml_baseline", ["# Local ML Baseline", "", "- status: `skipped`", "- reason: `requires at least two classes`"])
    vectorizer = TfidfVectorizer(max_features=5000)
    matrix = vectorizer.fit_transform(texts)
    model = LogisticRegression(max_iter=200, random_state=42)
    model.fit(matrix, labels)
    return write_result(
        "local_ml_baseline",
        ["# Local ML Baseline", "", "- status: `completed_smoke_fit`", f"- rows: `{len(rows)}`", "- note: `benchmark-only; no model artifact committed`"],
    )


def lexicon_comparison() -> Path:
    lexicon_paths = [ROOT / "data" / "external" / "loughran_mcdonald", ROOT / "data" / "lexicons"]
    exists = any(
        path.exists() and any(child.is_file() and child.name != ".gitkeep" for child in path.iterdir())
        for path in lexicon_paths
    )
    lines = ["# Lexicon Comparison", "", f"- status: `{'available' if exists else 'skipped'}`"]
    if not exists:
        lines.append("- reason: `Loughran-McDonald lexicon is not locally available; manual setup required.`")
    return write_result("lexicon_comparison", lines)


def dataset_comparison(rows: list[dict[str, object]]) -> Path:
    dataset_roots = [ROOT / "data" / "external" / "financial_phrasebank", ROOT / "data" / "external" / "goemotions"]
    local_files = [path for root in dataset_roots if root.exists() for path in root.glob("*") if path.is_file() and path.name != ".gitkeep"]
    lines = ["# Dataset Comparison", ""]
    if not local_files:
        lines.extend(["- status: `skipped`", "- reason: `No verified local dataset files found. No auto-download attempted.`"])
        return write_result("dataset_comparison", lines)
    counts = {}
    for row in rows:
        counts[row_label(row)] = counts.get(row_label(row), 0) + 1
    lines.extend(["- status: `completed_sanity_check`", f"- local_files: `{len(local_files)}`", "", "## Gold Label Distribution"])
    lines.extend(f"- `{label}`: {count}" for label, count in sorted(counts.items()))
    return write_result("dataset_comparison", lines)


def choose_experiment(gold_count: int) -> str:
    gates = gate_state(gold_count=gold_count, retrieval_experiment_mode=False, embedding_baseline_exists=False, evaluation_exists=False)
    if gates["local_ml"]:
        return "local_ml_baseline"
    return "deterministic_baseline"


def main() -> int:
    rows = valid_gold_rows(read_jsonl(GOLD_PATH))
    experiment = choose_experiment(len(rows))
    if experiment == "local_ml_baseline":
        path = local_ml_baseline(rows)
    else:
        path = deterministic_baseline(rows)
    lexicon_path = lexicon_comparison()
    dataset_path = dataset_comparison(rows)
    # Keep embedding benchmark gated and explicit; this call produces a skipped report unless gates are met.
    subprocess.run([sys.executable, str(TOOLS / "run_embedding_benchmark.py")], cwd=ROOT, check=False)
    print(json.dumps({"selected_experiment": experiment, "result": str(path), "lexicon_result": str(lexicon_path), "dataset_result": str(dataset_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
