from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_claims_matrix.py"


def test_claims_matrix_example_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", "configs/claims_matrix.example.yml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_unsupported_alpha_live_trading_stat_sig_claim_fails(tmp_path: Path) -> None:
    payload = {
        "claims": [
            {
                "claim": "Signal Engine produces statistically significant alpha for live trading.",
                "claim_type": "forbidden_claim",
                "status": "supported",
                "evidence_gate": "none",
                "notes": "",
            }
        ]
    }
    path = tmp_path / "bad_claims.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "must be not_supported" in result.stdout
