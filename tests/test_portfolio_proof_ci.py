from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_portfolio_proof.py"
LINK_CHECK_SCRIPT_PATH = ROOT / "scripts" / "check_markdown_links.py"


def test_build_portfolio_proof_skips_missing_legacy_bundle_without_overwriting_existing_proof(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "LLY_2025_Q2_call08"
    out_dir.mkdir()
    proof_path = out_dir / "portfolio_proof.json"
    original = '{"status":"existing"}\n'
    proof_path.write_text(original, encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out-dir",
            str(out_dir),
            "--proof-path",
            str(proof_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Portfolio proof build skipped" in completed.stdout
    assert "metrics.json" in completed.stdout
    assert "Leaving existing proof artifact untouched" in completed.stdout
    assert proof_path.read_text(encoding="utf-8") == original


def test_markdown_link_checker_passes_when_legacy_lly_outputs_are_not_referenced() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(LINK_CHECK_SCRIPT_PATH),
            "docs/demo-path.md",
            "docs/portfolio-proof.md",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Markdown link check warnings:" not in completed.stdout
    assert "Markdown link check passed." in completed.stdout
