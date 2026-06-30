#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from signal_engine.llm import LLMOutputValidationError, LLMRequest, load_llm_config, parse_and_validate_output, provider_for_name

PROMPTS = {
    "signal_candidates": ROOT / "prompts" / "earnings_signal_extraction.v1.md",
    "evidence_judge": ROOT / "prompts" / "evidence_judge.v1.md",
    "reviewer_packet_assist": ROOT / "prompts" / "reviewer_packet_assist.v1.md",
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _allowed_output_path(path: Path, allowed_roots: tuple[str, ...]) -> Path:
    resolved = path if path.is_absolute() else ROOT / path
    resolved = resolved.resolve()
    allowed = [(ROOT / root).resolve() for root in allowed_roots]
    if not any(resolved == root or resolved.is_relative_to(root) for root in allowed):
        allowed_text = ", ".join(str(root.relative_to(ROOT)) for root in allowed)
        raise ValueError(f"LLM output path must be under one of: {allowed_text}")
    return resolved


def _fixture_evidence(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    quote = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not quote:
        raise ValueError("fixture must contain at least one non-empty evidence quote")
    return [
        {
            "source_id": path.stem,
            "provenance_ref": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "speaker_role": "management",
            "transcript_section": "fixture_excerpt",
            "quote": quote,
        }
    ]


def _prompt(task: str, fixture: Path) -> str:
    prompt_path = PROMPTS[task]
    prompt_text = prompt_path.read_text(encoding="utf-8")
    fixture_text = fixture.read_text(encoding="utf-8")
    return f"{prompt_text}\n\nFixture excerpt:\n{fixture_text}"


def build_request(*, task: str, provider_name: str, fixture: Path) -> LLMRequest:
    return LLMRequest(
        request_id=f"fixture-smoke-{provider_name}-{task}",
        task=task,  # type: ignore[arg-type]
        provider=provider_name,
        model="configured-by-provider",
        prompt=_prompt(task, fixture),
        evidence=_fixture_evidence(fixture),
        metadata={"fixture": str(fixture.relative_to(ROOT)) if fixture.is_relative_to(ROOT) else str(fixture)},
    )


def run_smoke(*, provider_name: str, task: str, fixture: Path, out: Path, config_path: Path, live: bool) -> tuple[int, dict[str, Any]]:
    config = load_llm_config(config_path)
    out = _allowed_output_path(out, config.allowed_output_roots)
    request_payload = build_request(task=task, provider_name=provider_name, fixture=fixture)
    provider = provider_for_name(provider_name)
    result = provider.complete(request_payload, live=live and config.allow_live_provider_calls)

    artifact: dict[str, Any] = {
        "schema_version": "llm_fixture_smoke.v1",
        "status": result.status,
        "provider": result.provider,
        "model": result.model,
        "task": task,
        "canonical_output": False,
        "provider_calls_performed": result.provider_calls_performed,
        "message": result.message,
        "latency_seconds": result.latency_seconds,
        "estimated_cost_usd": result.estimated_cost_usd,
        "output": None,
        "validation_status": "not_run",
    }
    exit_code = 0
    if result.status == "ok":
        if task in {"signal_candidates", "evidence_judge"}:
            try:
                artifact["output"] = parse_and_validate_output(result.text, output_type=task)
                artifact["validation_status"] = "valid"
            except LLMOutputValidationError as exc:
                artifact["status"] = "invalid"
                artifact["message"] = str(exc)
                artifact["validation_status"] = "invalid"
                exit_code = 1
        else:
            artifact["output"] = json.loads(result.text)
            artifact["validation_status"] = "not_applicable"
    elif result.status == "error":
        exit_code = 1

    _write_json(out, artifact)
    return exit_code, artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an LLM fixture smoke test. Live calls are skipped unless explicitly enabled.")
    parser.add_argument("--provider", choices=["dry_run", "claude", "glm52"], default="dry_run")
    parser.add_argument("--task", choices=["signal_candidates", "evidence_judge", "reviewer_packet_assist"], default="signal_candidates")
    parser.add_argument("--fixture", default="tests/fixtures/tiny_realistic_earnings_excerpt.txt")
    parser.add_argument("--config", default="configs/llm.example.yml")
    parser.add_argument("--out", default="artifacts/llm/fixture_smoke.json")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)

    try:
        exit_code, artifact = run_smoke(
            provider_name=args.provider,
            task=args.task,
            fixture=(ROOT / args.fixture).resolve() if not Path(args.fixture).is_absolute() else Path(args.fixture).resolve(),
            out=Path(args.out),
            config_path=Path(args.config),
            live=args.live,
        )
    except Exception as exc:
        print(f"LLM fixture smoke failed: {type(exc).__name__}: {exc}")
        return 1

    print(
        "LLM fixture smoke "
        f"{artifact['status']}: provider={artifact['provider']} task={artifact['task']} "
        f"validation={artifact['validation_status']} calls={artifact['provider_calls_performed']}"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
