from __future__ import annotations

import re
from pathlib import Path

from tools.evaluate_retrieval import write_report


def test_summary_report_wording_distinguishes_smoke_from_production_claims(tmp_path: Path) -> None:
    report_path = tmp_path / "summary.md"
    write_report(
        {
            "smoke_metrics": True,
            "manifest_status": "not_provided",
            "warnings": ["smoke_metrics only; scaffold readiness check, not production retrieval quality evidence"],
            "failures": [],
            "rates": {},
        },
        report_path,
    )

    report = report_path.read_text(encoding="utf-8")

    assert "status is `smoke_metrics`" in report
    assert "evaluated_rag: `false`" in report
    assert "scaffold is ready for future reviewed retrieval eval queries" in report
    assert "not production RAG quality evidence" in report
    assert "No statistical, alpha, trading, live-execution, or market-causality claims" in report
    assert not re.search(r"evaluated\s+RAG", report, flags=re.IGNORECASE)
