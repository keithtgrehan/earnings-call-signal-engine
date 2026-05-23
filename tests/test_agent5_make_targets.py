from __future__ import annotations

from pathlib import Path


def test_agent_make_targets_are_present_and_safe() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    for target in (
        "agent5-rights-gated-discovery-check",
        "agent5-aggressive-acquisition-check",
        "build-nyse-5y-universe",
        "build-official-ir-candidate-map",
        "build-sec-metadata-queue",
        "build-webcast-metadata-queue",
        "build-source-availability-matrix",
        "agent5-acquisition-check",
        "gold-audit",
        "first-100-review-queue",
        "promotion-manifest-check",
        "agent1-pilot",
        "agent1-30-call-pilot",
        "agent2-evaluation-check",
    ):
        assert f"{target}:" in makefile
    unsafe_lines = [line for line in makefile.splitlines() if line.startswith(("agent5-", "agent1-", "gold-audit", "first-100"))]
    assert not any("yt-dlp" in line or "curl " in line or "wget " in line for line in unsafe_lines)
