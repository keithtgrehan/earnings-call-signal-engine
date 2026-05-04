#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from active_learning import select_review_batch  # noqa: E402
from alignment import align_records  # noqa: E402
from audio_engine import extract_audio_features  # noqa: E402
from data_layer import DATASET_CONNECTORS, NormalizedRecord, SegmentRecord, ingest_datasets  # noqa: E402
from data_layer.io import read_jsonl, write_json  # noqa: E402
from ensemble import build_ensemble_outputs  # noqa: E402
from fusion import fuse_modalities  # noqa: E402
from text_engine import score_text_segments  # noqa: E402
from training import evaluate_outputs, train_models  # noqa: E402
from video_engine import extract_video_features  # noqa: E402

STAGES = ("ingest", "align", "text", "audio", "video", "fusion", "ensemble", "train", "evaluate", "active-learning")


def _out_dir() -> Path:
    return ROOT / "data" / "processed" / "multimodal_engine"


def _status_path(stage: str) -> Path:
    return _out_dir() / f"{stage.replace('-', '_')}_status.json"


def _read_status(stage: str) -> dict[str, Any] | None:
    path = _status_path(stage)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_records() -> list[NormalizedRecord]:
    return [NormalizedRecord(**row) for row in read_jsonl(_out_dir() / "normalized_records.jsonl")]


def _load_segments() -> list[SegmentRecord]:
    return [SegmentRecord(**row) for row in read_jsonl(_out_dir() / "aligned_segments.jsonl")]


def _load_rows(name: str) -> list[dict[str, Any]]:
    return read_jsonl(_out_dir() / name)


def _dependency_readiness() -> dict[str, bool]:
    modules = [
        "pandas",
        "numpy",
        "sklearn",
        "pydantic",
        "regex",
        "spacy",
        "nltk",
        "transformers",
        "sentence_transformers",
        "datasets",
        "evaluate",
        "torch",
        "pytorch_lightning",
        "opensmile",
        "librosa",
        "pyannote.audio",
        "faster_whisper",
        "cv2",
        "mediapipe",
        "deepface",
        "torchvision",
        "snorkel",
        "deepeval",
        "faiss",
        "rank_bm25",
        "pyarrow",
        "orjson",
        "mlflow",
        "matplotlib",
        "seaborn",
        "plotly",
    ]
    return {module: importlib.util.find_spec(module) is not None for module in modules}


def _write_docs(output_dir: Path, statuses: dict[str, Any]) -> None:
    docs = ROOT / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    status_summary = {
        key: value.get("status") or ("completed" if key == "ingest" and value.get("schema_version") else "unknown")
        for key, value in statuses.items()
        if isinstance(value, dict)
    }
    training_status = statuses.get("train", {})
    evaluation_status = statuses.get("evaluate", {})
    fusion_status = statuses.get("fusion", {})
    ensemble_status = statuses.get("ensemble", {})
    architecture = """# System Architecture

The Multimodal Communication Intelligence Engine is transcript-first. Text rules, weak labels, and local classifiers form the anchor; audio and video add bounded segment-level evidence when present.

## Pipeline

1. Ingest manifest-backed public, local, and gated dataset connectors.
2. Normalize every accepted row into the canonical v1 record schema and preserve rejected rows separately.
3. Align records into segment records with transcript-first timestamps and optional ASR/diarization readiness.
4. Score text signals, weak labels, emotion, and sentiment.
5. Extract audio/video features only when media exists and the event gate allows it.
6. Fuse modality evidence with text as anchor.
7. Ensemble all visible votes and disagreement flags.
8. Train/evaluate only when label support is honest enough.
9. Select a minimal active-learning review batch.

## Current Boundary

No API keys are required for the core path. Missing heavyweight or gated datasets/models are recorded as explicit skipped statuses. The current local fixture run does not include real audio/video-backed training data, so audio/video stages report limitation-aware outputs until aligned media is added.
"""
    evaluation = f"""# Evaluation Results

Evaluation artifacts live in `{output_dir}`.

The current smoke evaluation is a reproducibility and wiring check, not a gold-label performance claim. Text model metrics are bounded to the current local human-reviewed seed labels. A validated model requires a real held-out benchmark with stable splits.

## Stage Summary

```json
{json.dumps(status_summary, indent=2)}
```

## Claim Boundary

- Self-consistency rows prove the pipeline runs end to end.
- Text model metrics are bounded to the current local human-reviewed seed set.
- Multimodal uplift and cross-domain degradation remain explicit `requires labels` outputs until aligned multimodal gold labels exist.
- Weak labels, model predictions, and optional LLM triage are not gold labels.
"""
    performance = f"""# Model Performance

Model artifacts root: `{ROOT / "models" / "multimodal_engine"}`.

The current text baseline is a fixture/seed-label baseline. It proves the training and tracking loop, but it is not a validated model and should not be presented as production performance.

## Training Status

```json
{json.dumps(training_status, indent=2)}
```

The v1 run trains TF-IDF sklearn text baselines when local human-reviewed signal labels satisfy class-support gates. Logistic Regression, Random Forest, and shallow PyTorch multimodal models are registered as candidates but are not trained without aligned multimodal gold labels.
"""
    multimodal = f"""# Multimodal Analysis

Principle: `TEXT = anchor; AUDIO + VIDEO = augmentation layers`.

## Fusion

```json
{json.dumps(fusion_status, indent=2)}
```

## Ensemble

```json
{json.dumps(ensemble_status, indent=2)}
```

Audio and video outputs preserve `available`, `limitations`, and adapter metadata per segment. Side cues never override text evidence and disagreement remains visible in the ensemble output.

Current limitation: the fixture run has no local audio/video-backed training data. Multimodal uplift remains unproven until aligned media and human gold labels exist.
"""
    handoff = f"""# Implementation Handoff

## Commands

```bash
python tools/run_full_pipeline.py --dry-run
python tools/run_full_pipeline.py --stage all
pytest
ruff check .
```

## Primary Outputs

- Processed artifacts: `{output_dir}`
- Ensemble output: `{output_dir / "ensemble_outputs.jsonl"}`
- Review batch: `{output_dir / "next_review_batch.csv"}`
- Training status: `{output_dir / "training_status.json"}`
- Evaluation status: `{output_dir / "evaluation_results.json"}`

## Current Evaluation Snapshot

```json
{json.dumps(evaluation_status, indent=2)}
```

## Notes For The Next Builder

- Add local dataset files under `data/external/*.jsonl` using the connector names in `src/data_layer/ingestion.py`.
- Add aligned audio/video paths to normalized rows before expecting multimodal uplift.
- Keep gold labels separate from weak/model/synthetic provenance.
- Use `docs/project_goals_and_scope.md`, `docs/roadmap_to_trained_model.md`, `docs/compute_strategy.md`, and `docs/codex_project_context.md` as the scope guardrails.
"""
    (docs / "system_architecture.md").write_text(architecture, encoding="utf-8")
    (docs / "evaluation_results.md").write_text(evaluation, encoding="utf-8")
    (docs / "model_performance.md").write_text(performance, encoding="utf-8")
    (docs / "multimodal_analysis.md").write_text(multimodal, encoding="utf-8")
    (docs / "implementation_handoff.md").write_text(handoff, encoding="utf-8")


def _maybe_skip(stage: str, resume: bool) -> bool:
    return resume and _read_status(stage) is not None


def run_pipeline(*, stage: str, dry_run: bool = False, resume: bool = False) -> dict[str, Any]:
    output_dir = _out_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    requested = STAGES if stage == "all" else (stage,)
    statuses: dict[str, Any] = {}
    records: list[NormalizedRecord] = []
    segments: list[SegmentRecord] = []
    text_rows: list[dict[str, Any]] = []
    audio_rows: list[dict[str, Any]] = []
    video_rows: list[dict[str, Any]] = []
    fusion_rows: list[dict[str, Any]] = []
    ensemble_rows: list[dict[str, Any]] = []

    dry_run_status = {
        "stage": "dry-run",
        "status": "completed",
        "dataset_connectors": [connector.dataset_id for connector in DATASET_CONNECTORS],
        "dependency_readiness": _dependency_readiness(),
        "output_dir": str(output_dir),
    }
    if dry_run:
        ingest_result = ingest_datasets(root=ROOT, output_dir=output_dir, dry_run=True)
        dry_run_status["ingestion_manifest"] = ingest_result["manifest"]
        write_json(output_dir / "dry_run_status.json", dry_run_status)
        return {"status": "completed", "dry_run": dry_run_status}

    if "ingest" in requested:
        if _maybe_skip("ingest", resume):
            statuses["ingest"] = _read_status("ingest") or {}
        else:
            ingest_result = ingest_datasets(root=ROOT, output_dir=output_dir)
            statuses["ingest"] = ingest_result["manifest"]
            write_json(_status_path("ingest"), {"stage": "ingest", "status": "completed", **ingest_result["manifest"]})
        records = _load_records()

    if "align" in requested:
        records = records or _load_records()
        result = align_records(records, output_dir=output_dir)
        statuses["align"] = result["status"]
        segments = result["segments"]

    if "text" in requested:
        segments = segments or _load_segments()
        result = score_text_segments(segments, output_dir=output_dir)
        statuses["text"] = result["status"]
        text_rows = result["rows"]

    if "audio" in requested:
        segments = segments or _load_segments()
        result = extract_audio_features(segments, output_dir=output_dir)
        statuses["audio"] = result["status"]
        audio_rows = result["rows"]

    if "video" in requested:
        segments = segments or _load_segments()
        text_rows = text_rows or _load_rows("text_predictions.jsonl")
        result = extract_video_features(segments, text_rows=text_rows, output_dir=output_dir)
        statuses["video"] = result["status"]
        video_rows = result["rows"]

    if "fusion" in requested:
        text_rows = text_rows or _load_rows("text_predictions.jsonl")
        audio_rows = audio_rows or _load_rows("audio_features.jsonl")
        video_rows = video_rows or _load_rows("video_features.jsonl")
        result = fuse_modalities(text_rows=text_rows, audio_rows=audio_rows, video_rows=video_rows, output_dir=output_dir)
        statuses["fusion"] = result["status"]
        fusion_rows = result["rows"]

    if "ensemble" in requested:
        text_rows = text_rows or _load_rows("text_predictions.jsonl")
        fusion_rows = fusion_rows or _load_rows("fusion_predictions.jsonl")
        result = build_ensemble_outputs(text_rows=text_rows, fusion_rows=fusion_rows, output_dir=output_dir)
        statuses["ensemble"] = result["status"]
        ensemble_rows = result["rows"]

    if "train" in requested:
        result = train_models(root=ROOT, output_dir=output_dir)
        statuses["train"] = result["summary"]

    if "evaluate" in requested:
        ensemble_rows = ensemble_rows or _load_rows("ensemble_outputs.jsonl")
        result = evaluate_outputs(ensemble_rows=ensemble_rows, output_dir=output_dir)
        statuses["evaluate"] = result["report"]

    if "active-learning" in requested:
        ensemble_rows = ensemble_rows or _load_rows("ensemble_outputs.jsonl")
        result = select_review_batch(ensemble_rows, output_dir=output_dir)
        statuses["active-learning"] = result["status"]

    _write_docs(output_dir, statuses)
    write_json(output_dir / "pipeline_status.json", {"stage": stage, "status": "completed", "statuses": statuses})
    return {"status": "completed", "statuses": statuses}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the multimodal communication intelligence engine pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Validate readiness without heavy processing.")
    parser.add_argument("--resume", action="store_true", help="Reuse completed stage artifacts when present.")
    parser.add_argument("--stage", default="all", choices=(*STAGES, "all"), help="Stage to run.")
    args = parser.parse_args(argv)
    result = run_pipeline(stage=args.stage, dry_run=args.dry_run, resume=args.resume)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
