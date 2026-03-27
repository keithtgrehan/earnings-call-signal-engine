from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from earnings_call_sentiment.model_sidecars import runner
from earnings_call_sentiment.model_sidecars.models.base import (
    BaseClassificationSidecar,
    ClassificationOutput,
    LabelScore,
    TextUnit,
)


class FakeClassificationSidecar(BaseClassificationSidecar):
    key = "fake_classification"
    model_id = "fake/model"

    def __init__(self, *, device: str = "cpu") -> None:
        super().__init__(device=device)
        self.predict_calls = 0
        self.prewarm_calls = 0
        self.seen_source_ids: list[list[str]] = []

    def prewarm(self) -> dict[str, object]:
        self.prewarm_calls += 1
        return {
            "model_name": self.key,
            "model_id": self.model_id,
            "output_kind": self.output_kind,
            "device": self.device,
        }

    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = 8,
        max_length: int = 512,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationOutput]:
        del batch_size, max_length, label_groups
        self.predict_calls += 1
        self.seen_source_ids.append([unit.source_id for unit in units])
        return [
            ClassificationOutput(
                unit=unit,
                scores=[LabelScore(label="positive", score=0.9, rank=1)],
            )
            for unit in units
        ]


def _patch_case(monkeypatch, tmp_path: Path, units: list[TextUnit]) -> None:
    case = SimpleNamespace(case_id="synthetic_case", input_root=tmp_path / "case")
    monkeypatch.setattr(
        runner,
        "resolve_case_artifacts",
        lambda case_id, case_dir=None: case,
    )
    monkeypatch.setattr(
        runner,
        "load_units_for_case",
        lambda case, unit_types: {unit_type: list(units) for unit_type in unit_types},
    )


def test_prewarm_model_sidecars_returns_warmed_summary(
    monkeypatch,
) -> None:
    instances: list[FakeClassificationSidecar] = []

    def _build_model(name: str, *, device: str = "auto") -> FakeClassificationSidecar:
        del name
        instance = FakeClassificationSidecar(device=device)
        instances.append(instance)
        return instance

    monkeypatch.setattr(runner, "build_model", _build_model)

    payload = runner.prewarm_model_sidecars(
        model_names=["finbert_tone"],
        device="cpu",
    )

    assert payload["warmed_models"] == ["fake_classification"]
    assert not payload["failed_models"]
    assert instances[0].prewarm_calls == 1


def test_run_model_sidecars_skips_completed_outputs_and_force_recomputes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    units = [
        TextUnit(
            case_id="synthetic_case",
            unit_type="chunks",
            source_id="chunk-1",
            text="Demand remains stable.",
        )
    ]
    _patch_case(monkeypatch, tmp_path, units)
    instances: list[FakeClassificationSidecar] = []

    def _build_model(name: str, *, device: str = "auto") -> FakeClassificationSidecar:
        del name
        instance = FakeClassificationSidecar(device=device)
        instances.append(instance)
        return instance

    monkeypatch.setattr(runner, "build_model", _build_model)

    first = runner.run_model_sidecars(
        case_ids=["synthetic_case"],
        model_names=["finbert_tone"],
        unit_types=["chunks"],
        output_dir=tmp_path / "outputs",
    )
    assert first["cases"][0]["models"]["finbert_tone"]["unit_results"]["chunks"]["status"] == "completed"
    assert instances[0].predict_calls == 1

    second = runner.run_model_sidecars(
        case_ids=["synthetic_case"],
        model_names=["finbert_tone"],
        unit_types=["chunks"],
        output_dir=tmp_path / "outputs",
    )
    assert second["cases"][0]["models"]["finbert_tone"]["unit_results"]["chunks"]["status"] == "skipped_existing"
    assert instances[1].predict_calls == 0

    third = runner.run_model_sidecars(
        case_ids=["synthetic_case"],
        model_names=["finbert_tone"],
        unit_types=["chunks"],
        output_dir=tmp_path / "outputs",
        force=True,
    )
    assert third["cases"][0]["models"]["finbert_tone"]["unit_results"]["chunks"]["status"] == "completed"
    assert instances[2].predict_calls == 1


def test_run_model_sidecars_recomputes_after_partial_inprogress_artifact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    units = [
        TextUnit(
            case_id="synthetic_case",
            unit_type="chunks",
            source_id="chunk-1",
            text="Demand remains stable.",
        )
    ]
    _patch_case(monkeypatch, tmp_path, units)
    instances: list[FakeClassificationSidecar] = []

    def _build_model(name: str, *, device: str = "auto") -> FakeClassificationSidecar:
        del name
        instance = FakeClassificationSidecar(device=device)
        instances.append(instance)
        return instance

    monkeypatch.setattr(runner, "build_model", _build_model)

    model_dir = tmp_path / "outputs" / "synthetic_case" / "model_sidecars" / "finbert_tone"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / ".chunk_scores.jsonl.inprogress").write_text(
        '{"partial": true}\n',
        encoding="utf-8",
    )

    payload = runner.run_model_sidecars(
        case_ids=["synthetic_case"],
        model_names=["finbert_tone"],
        unit_types=["chunks"],
        output_dir=tmp_path / "outputs",
    )

    assert payload["cases"][0]["models"]["finbert_tone"]["unit_results"]["chunks"]["status"] == "completed"
    assert instances[0].predict_calls == 1
    assert (model_dir / "chunk_scores.jsonl").exists()


def test_run_model_sidecars_applies_limit_and_seeded_random_sampling(
    monkeypatch,
    tmp_path: Path,
) -> None:
    units = [
        TextUnit(
            case_id="synthetic_case",
            unit_type="chunks",
            source_id=f"chunk-{index}",
            text=f"row {index}",
            section="prepared_remarks" if index < 3 else "q_and_a",
        )
        for index in range(6)
    ]
    _patch_case(monkeypatch, tmp_path, units)
    instances: list[FakeClassificationSidecar] = []

    def _build_model(name: str, *, device: str = "auto") -> FakeClassificationSidecar:
        del name
        instance = FakeClassificationSidecar(device=device)
        instances.append(instance)
        return instance

    monkeypatch.setattr(runner, "build_model", _build_model)

    runner.run_model_sidecars(
        case_ids=["synthetic_case"],
        model_names=["finbert_tone"],
        unit_types=["chunks"],
        output_dir=tmp_path / "outputs-a",
        limit=4,
        sample_size=2,
        sample_strategy="random",
        seed=19,
        force=True,
    )
    first_ids = instances[0].seen_source_ids[0]

    runner.run_model_sidecars(
        case_ids=["synthetic_case"],
        model_names=["finbert_tone"],
        unit_types=["chunks"],
        output_dir=tmp_path / "outputs-b",
        limit=4,
        sample_size=2,
        sample_strategy="random",
        seed=19,
        force=True,
    )
    second_ids = instances[1].seen_source_ids[0]

    assert first_ids == second_ids
    assert len(first_ids) == 2
    assert set(first_ids).issubset({"chunk-0", "chunk-1", "chunk-2", "chunk-3"})
