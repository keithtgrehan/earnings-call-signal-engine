from pathlib import Path
import importlib.util
import shutil


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "portfolio" / "validate_control_room.py"
SPEC = importlib.util.spec_from_file_location("validate_control_room", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_foundation_contract_is_complete() -> None:
    assert MODULE.validate(ROOT) == []


def test_release_contract_fails_closed_until_artifacts_exist() -> None:
    errors = MODULE.validate(ROOT, release=True)
    assert any("missing release artifact" in error for error in errors)
    assert any("unchecked release gates" in error for error in errors)


def test_missing_root_reports_required_files(tmp_path: Path) -> None:
    errors = MODULE.validate(tmp_path)
    assert any("missing control-room document" in error for error in errors)
    assert any("missing repository automation file" in error for error in errors)


def copy_foundation(tmp_path: Path) -> Path:
    for relative in MODULE.REQUIRED_REPO_FILES:
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    docs_destination = tmp_path / "docs" / "portfolio_v1"
    docs_destination.mkdir(parents=True, exist_ok=True)
    for name in MODULE.REQUIRED_DOCS:
        shutil.copy2(ROOT / "docs" / "portfolio_v1" / name, docs_destination / name)
    return tmp_path


def test_unpinned_github_action_fails_closed(tmp_path: Path) -> None:
    root = copy_foundation(tmp_path)
    workflow = root / ".github" / "workflows" / "portfolio-v1.yml"
    original = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
    workflow.write_text(workflow.read_text(encoding="utf-8").replace(original, "actions/checkout@v4"), encoding="utf-8")
    errors = MODULE.validate(root)
    assert any("pinned to a 40-character SHA" in error for error in errors)


def test_missing_instruction_marker_fails_closed(tmp_path: Path) -> None:
    root = copy_foundation(tmp_path)
    agents = root / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace("## Portfolio Product V1 Control Room", "## Removed marker"),
        encoding="utf-8",
    )
    errors = MODULE.validate(root)
    assert any("missing required marker" in error for error in errors)
