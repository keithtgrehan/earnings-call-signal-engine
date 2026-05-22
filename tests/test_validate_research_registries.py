import csv
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_research_registries.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_research_registries", VALIDATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def copy_rows(source_path):
    with source_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames, list(reader)


def messages(result):
    return "\n".join(error["message"] for error in result["errors"])


def test_current_source_registry_validates_successfully():
    validator = load_validator()
    result = validator.validate_source_registry(REPO_ROOT)
    assert result["ok"], messages(result)
    assert result["row_counts"]["data/research/llm_quant_source_registry.csv"] == 14


def test_current_feature_backlog_validates_successfully():
    validator = load_validator()
    result = validator.validate_feature_backlog(REPO_ROOT)
    assert result["ok"], messages(result)
    assert result["row_counts"]["data/research/future_feature_backlog.csv"] == 36


def test_current_dataset_targets_validates_successfully():
    validator = load_validator()
    result = validator.validate_dataset_targets(REPO_ROOT)
    assert result["ok"], messages(result)
    assert result["row_counts"]["data/research/future_dataset_targets.csv"] == 16


def test_validate_all_returns_json_ready_shape():
    validator = load_validator()
    result = validator.validate_all(REPO_ROOT)
    assert set(result) == {"ok", "files_checked", "errors", "warnings", "row_counts"}
    assert result["ok"] is True
    assert len(result["files_checked"]) == 3
    assert result["errors"] == []


def test_exact_header_validation_reports_mismatch(tmp_path):
    validator = load_validator()
    header, rows = copy_rows(
        REPO_ROOT / "data" / "research" / "llm_quant_source_registry.csv"
    )
    bad_header = list(header)
    bad_header[0] = "bad_source_id"
    path = tmp_path / "source.csv"
    write_csv(path, bad_header, rows)

    loaded = validator.load_csv(path)
    errors = []
    validator.validate_headers(
        str(path), loaded["headers"], validator.SOURCE_REGISTRY_HEADER, errors
    )

    assert errors
    assert errors[0]["field"] == "header"
    assert "exact header mismatch" in errors[0]["message"]


def test_required_ids_present_reports_missing_id(tmp_path):
    validator = load_validator()
    header, rows = copy_rows(
        REPO_ROOT / "data" / "research" / "llm_quant_source_registry.csv"
    )
    rows = [
        row
        for row in rows
        if row["source_id"] != "man_alphagpt_external_reporting"
    ]
    path = tmp_path / "source.csv"
    write_csv(path, header, rows)

    result = validator.validate_source_registry(REPO_ROOT, path_override=path)

    assert not result["ok"]
    assert "missing required source_id: man_alphagpt_external_reporting" in messages(
        result
    )


def test_duplicate_id_detection_uses_tmp_csv(tmp_path):
    validator = load_validator()
    header, rows = copy_rows(
        REPO_ROOT / "data" / "research" / "future_feature_backlog.csv"
    )
    rows[1]["feature_id"] = rows[0]["feature_id"]
    path = tmp_path / "features.csv"
    write_csv(path, header, rows)

    result = validator.validate_feature_backlog(REPO_ROOT, path_override=path)

    assert not result["ok"]
    assert "duplicate feature_id" in messages(result)


def test_invalid_enum_detection_uses_tmp_csv(tmp_path):
    validator = load_validator()
    header, rows = copy_rows(
        REPO_ROOT / "data" / "research" / "future_dataset_targets.csv"
    )
    rows[0]["training_allowed"] = "always_train"
    path = tmp_path / "datasets.csv"
    write_csv(path, header, rows)

    result = validator.validate_dataset_targets(REPO_ROOT, path_override=path)

    assert not result["ok"]
    assert "invalid enum value" in messages(result)
    assert "training_allowed" in messages(result)


def test_missing_required_field_detection_uses_tmp_csv(tmp_path):
    validator = load_validator()
    header, rows = copy_rows(
        REPO_ROOT / "data" / "research" / "future_feature_backlog.csv"
    )
    rows[0]["required_inputs"] = ""
    path = tmp_path / "features.csv"
    write_csv(path, header, rows)

    result = validator.validate_feature_backlog(REPO_ROOT, path_override=path)

    assert not result["ok"]
    assert "required field is empty" in messages(result)
    assert "required_inputs" in messages(result)


def test_unsafe_claim_language_detection_uses_tmp_csv(tmp_path):
    validator = load_validator()
    header, rows = copy_rows(
        REPO_ROOT / "data" / "research" / "future_dataset_targets.csv"
    )
    rows[0]["primary_use"] = "guaranteed alpha for training readiness"
    path = tmp_path / "datasets.csv"
    write_csv(path, header, rows)

    result = validator.validate_dataset_targets(REPO_ROOT, path_override=path)

    assert not result["ok"]
    assert "unsupported claim language" in messages(result)


def test_invalid_url_detection_for_source_registry_uses_tmp_csv(tmp_path):
    validator = load_validator()
    header, rows = copy_rows(
        REPO_ROOT / "data" / "research" / "llm_quant_source_registry.csv"
    )
    rows[0]["url"] = "http://example.com/not-https"
    path = tmp_path / "source.csv"
    write_csv(path, header, rows)

    result = validator.validate_source_registry(REPO_ROOT, path_override=path)

    assert not result["ok"]
    assert "url must start with https://" in messages(result)
