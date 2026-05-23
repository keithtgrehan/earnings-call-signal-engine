from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_affective_research_registries.py"
MODEL_REGISTRY = ROOT / "configs" / "affective_model_registry.example.yml"
DATASET_REGISTRY = ROOT / "configs" / "affective_dataset_registry.example.yml"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_affective_research_registries", VALIDATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def messages(result: dict) -> str:
    return "\n".join(result["errors"])


def write_payload(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "registry.yml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_affective_model_registry_validates() -> None:
    validator = load_validator()
    result = validator.validate_registry(MODEL_REGISTRY)

    assert result["status"] == "valid", messages(result)


def test_affective_dataset_registry_validates() -> None:
    validator = load_validator()
    result = validator.validate_registry(DATASET_REGISTRY)

    assert result["status"] == "valid", messages(result)


def test_training_allowed_false_unless_explicit(tmp_path: Path) -> None:
    validator = load_validator()
    payload = yaml.safe_load(MODEL_REGISTRY.read_text(encoding="utf-8"))
    payload["entries"][0]["training_allowed"] = True
    path = write_payload(tmp_path, payload)

    result = validator.validate_registry(path)

    assert result["status"] == "invalid"
    assert "training_allowed must stay false" in messages(result)


def test_blocked_prohibited_uses_are_blocked(tmp_path: Path) -> None:
    validator = load_validator()
    payload = yaml.safe_load(MODEL_REGISTRY.read_text(encoding="utf-8"))
    payload["entries"][0]["workplace_education_prohibited_use"] = False
    path = write_payload(tmp_path, payload)

    result = validator.validate_registry(path)

    assert result["status"] == "invalid"
    assert "workplace/education emotion inference must be blocked" in messages(result)


def test_no_true_emotion_inference_claim(tmp_path: Path) -> None:
    validator = load_validator()
    payload = yaml.safe_load(MODEL_REGISTRY.read_text(encoding="utf-8"))
    payload["entries"][0]["legal_notes"] = (
        "This entry infers true internal emotion inference from cues; "
        "no deception detection; no biometric identity inference; "
        "workplace/education emotion inference prohibited."
    )
    path = write_payload(tmp_path, payload)

    result = validator.validate_registry(path)

    assert result["status"] == "invalid"
    assert "true internal emotion inference" in messages(result)


def test_no_deception_detection(tmp_path: Path) -> None:
    validator = load_validator()
    payload = yaml.safe_load(DATASET_REGISTRY.read_text(encoding="utf-8"))
    payload["entries"][0]["legal_notes"] = (
        "Observable cues only; no true internal emotion inference; "
        "deception detection allowed; no biometric identity inference; "
        "workplace/education emotion inference prohibited."
    )
    path = write_payload(tmp_path, payload)

    result = validator.validate_registry(path)

    assert result["status"] == "invalid"
    assert "deception detection" in messages(result)


def test_no_biometric_identity_inference(tmp_path: Path) -> None:
    validator = load_validator()
    payload = copy.deepcopy(yaml.safe_load(DATASET_REGISTRY.read_text(encoding="utf-8")))
    payload["entries"][0]["legal_notes"] = (
        "Observable cues only; no true internal emotion inference; "
        "no deception detection; biometric identity inference allowed; "
        "workplace/education emotion inference prohibited."
    )
    path = write_payload(tmp_path, payload)

    result = validator.validate_registry(path)

    assert result["status"] == "invalid"
    assert "biometric identity inference" in messages(result)
