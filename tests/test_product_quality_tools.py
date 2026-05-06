from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from evaluation_quality import read_jsonl, source_group  # noqa: E402
from signal_engine.signal_baseline import predict_deterministic_signal_family  # noqa: E402


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(ROOT / "tools" / args[0]), *args[1:]], cwd=ROOT, text=True, capture_output=True, check=True)


def test_source_quality_group_derivation() -> None:
    rows = read_jsonl(ROOT / "data" / "gold" / "gold_labels.jsonl")
    assert any(source_group(row) == "fixture" for row in rows)
    assert any(source_group(row) == "human_reviewed" for row in rows)
    assert any(source_group(row) == "imported_guidance" for row in rows)


def test_filter_gold_labels_does_not_mutate_canonical(tmp_path: Path) -> None:
    canonical = ROOT / "data" / "gold" / "gold_labels.jsonl"
    before = canonical.read_text(encoding="utf-8")
    out = tmp_path / "filtered.jsonl"
    result = run_tool("filter_gold_labels.py", "--source", "human_reviewed", "--out", str(out))
    payload = json.loads(result.stdout)
    assert payload["rows"] > 0
    assert out.exists()
    assert canonical.read_text(encoding="utf-8") == before


def test_deterministic_refinement_known_examples() -> None:
    assert (
        predict_deterministic_signal_family("If the rollout stabilizes this quarter")["label"]
        == "uncertainty_hedging"
    )
    assert (
        predict_deterministic_signal_family("the current status is that procurement is scheduled for next Tuesday")["label"]
        == "neutral"
    )
    assert (
        predict_deterministic_signal_family("We expect revenue of 80.65 to 81.75 billion US dollars")["label"]
        == "uncertainty_hedging"
    )
    assert predict_deterministic_signal_family("guidance is flat")["label"] == "opportunity_commitment"


def test_evidence_objects_and_retrieval_skip(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.jsonl"
    run_tool("build_evidence_objects.py", "--out", str(evidence))
    rows = read_jsonl(evidence)
    assert rows
    required = {
        "case_id",
        "speaker",
        "section",
        "text",
        "gold_label",
        "deterministic_label",
        "deterministic_score",
        "source_group",
        "provenance_quality",
        "requires_manual_review",
    }
    assert required <= set(rows[0])
    result = run_tool("run_retrieval_benchmark.py", "--evidence", str(evidence))
    payload = json.loads(result.stdout)
    assert payload["status"] == "skipped"
    assert ">=100" in payload["reason"]


def test_false_positive_cluster_and_demo_tools_run() -> None:
    cluster = run_tool("cluster_false_positives.py")
    assert json.loads(cluster.stdout)["status"] == "ok"
    demo = run_tool("build_demo_artifacts.py")
    assert json.loads(demo.stdout)["status"] == "ok"
    assert (ROOT / "reports" / "demo" / "analyst_report_LLY_2025_Q2_call08.md").exists()
