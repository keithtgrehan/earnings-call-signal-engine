from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from earnings_call_sentiment.model_sidecars.evaluate import write_evaluation_outputs


def _prepare_sidecar_outputs(tmp_path: Path) -> Path:
    case_root = tmp_path / "outputs" / "synthetic_case" / "model_sidecars"
    for model_name in ("finbert_tone", "financial_roberta", "mpnet_embeddings"):
        model_dir = case_root / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "run_summary.json").write_text(
            json.dumps(
                {
                    "runtime_s": 1.2,
                    "unit_counts": {"chunks": 1},
                    "label_distributions": {"chunks": {"positive": 1}},
                    "vector_dimensions": {"chunks": 3},
                }
            ),
            encoding="utf-8",
        )

    (case_root / "finbert_tone" / "chunk_scores.jsonl").write_text(
        json.dumps(
            {
                "case_id": "synthetic_case",
                "unit_type": "chunks",
                "source_id": "row-1",
                "section": "presentation",
                "speaker": "CEO",
                "text": "Demand remains stable.",
                "model_name": "finbert_tone",
                "label": "positive",
                "score": 0.91,
                "rank": 1,
                "metadata": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (case_root / "financial_roberta" / "chunk_scores.jsonl").write_text(
        json.dumps(
            {
                "case_id": "synthetic_case",
                "unit_type": "chunks",
                "source_id": "row-1",
                "section": "presentation",
                "speaker": "CEO",
                "text": "Demand remains stable.",
                "model_name": "financial_roberta",
                "label": "negative",
                "score": 0.87,
                "rank": 1,
                "metadata": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (case_root / "mpnet_embeddings" / "chunk_similarity.json").write_text(
        json.dumps(
            {
                "mode": "within_case",
                "unit_type": "chunks",
                "neighbors": [
                    {
                        "source_id": "row-1",
                        "text": "Demand remains stable.",
                        "nearest_neighbors": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return case_root


def test_write_evaluation_outputs_writes_json_and_markdown(tmp_path: Path) -> None:
    _prepare_sidecar_outputs(tmp_path)

    artifacts = write_evaluation_outputs(
        "synthetic_case",
        sidecar_root=tmp_path / "outputs",
    )

    payload = json.loads(artifacts["json_path"].read_text(encoding="utf-8"))
    assert payload["case_id"] == "synthetic_case"
    assert payload["finbert_vs_financial_roberta"]["disagreement_rows"] == 1
    assert artifacts["md_path"].exists()


def test_evaluate_model_sidecars_script_runs(tmp_path: Path) -> None:
    _prepare_sidecar_outputs(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    script_path = repo_root / "scripts" / "evaluate_model_sidecars.py"

    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--case-id",
            "synthetic_case",
            "--sidecar-root",
            str(tmp_path / "outputs"),
        ],
        cwd=str(repo_root),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert "artifacts" in payload
