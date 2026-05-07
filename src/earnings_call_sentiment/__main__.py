from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys


def _run_lightweight_help() -> int:
    print(
        """usage: earnings-call-sentiment [options]

Analyze earnings call sentiment from transcripts and optional video input.

options:
  --youtube-url YOUTUBE_URL
  --audio-path AUDIO_PATH
  --symbol SYMBOL
  --event-dt EVENT_DT
  --cache-dir CACHE_DIR
  --out-dir OUT_DIR
  --download-only
  --question-shifts      Detect question-related sentiment shifts and write CSV/PNG outputs.
  --prior-guidance PRIOR_GUIDANCE
  --tone-change-threshold TONE_CHANGE_THRESHOLD
  --vad
  --force
  --resume
  --strict
  --sentiment-model SENTIMENT_MODEL
  --sentiment-revision SENTIMENT_REVISION
  --llm-summary
  --summary-provider SUMMARY_PROVIDER
  --summary-model SUMMARY_MODEL
  --summary-base-url SUMMARY_BASE_URL
  --summary-api-key-env SUMMARY_API_KEY_ENV
  --summary-timeout-s SUMMARY_TIMEOUT_S
"""
    )
    return 0


def _run_lightweight_dry_run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="earnings-call-sentiment")
    parser.add_argument("--youtube-url", default=None)
    parser.add_argument("--audio-path", default=None)
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--event-dt", default=None)
    parser.add_argument("--cache-dir", default="./cache")
    parser.add_argument("--out-dir", default="./outputs")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--force", action="store_true", default=False)
    parser.add_argument("--prior-guidance", default=None)
    parser.add_argument("--sentiment-model", default="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    parser.add_argument("--sentiment-revision", default="714eb0f")
    parser.add_argument("--llm-summary", action="store_true", default=False)
    parser.add_argument("--summary-provider", default=None)
    parser.add_argument("--summary-model", default=None)
    parser.add_argument("--summary-base-url", default=None)
    parser.add_argument("--summary-api-key-env", default=None)
    parser.add_argument("--summary-timeout-s", type=float, default=30.0)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--download-only", action="store_true", default=False)
    parser.add_argument("--transcribe-only", action="store_true", default=False)
    parser.add_argument("--score-only", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--question-shifts", action="store_true", default=False)
    args, _unknown = parser.parse_known_args(argv)
    if not args.youtube_url and not args.audio_path:
        parser.error("--youtube-url is required when --audio-path is not provided")
    provider = args.summary_provider or ("openai_compatible" if args.llm_summary else "none")
    summary_ok = not args.llm_summary
    summary_message = "Summary disabled; optional summary stage is skipped." if summary_ok else "Summary requested; full CLI preflight skipped in module dry-run."
    event_dt = args.event_dt or datetime.now(UTC).astimezone().isoformat()
    print("Dry run enabled; skipping execution.")
    print(f"youtube_url={args.youtube_url}")
    print(f"audio_path={args.audio_path}")
    print(f"cache_dir={Path(args.cache_dir).expanduser().resolve()}")
    print(f"out_dir={Path(args.out_dir).expanduser().resolve()}")
    print(f"resume={args.resume}")
    print(f"force={args.force}")
    print(f"prior_guidance={args.prior_guidance}")
    print(f"sentiment_model={args.sentiment_model}")
    print(f"sentiment_revision={args.sentiment_revision}")
    print(f"symbol={str(args.symbol or '').strip().upper() or 'UNKNOWN'}")
    print(f"event_dt={event_dt}")
    print(f"summary_enabled={bool(args.llm_summary)}")
    print(f"summary_provider={provider}")
    print(f"summary_model={args.summary_model}")
    print(f"summary_base_url={args.summary_base_url}")
    print(f"summary_api_key_env={args.summary_api_key_env}")
    print(f"summary_timeout_s={args.summary_timeout_s}")
    print(f"summary_preflight_ok={summary_ok}")
    print(f"summary_preflight_message={summary_message}")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    if any(arg in {"--help", "-h"} for arg in raw_args) and not (raw_args and raw_args[0].startswith("sidecars")):
        return _run_lightweight_help()
    if "--dry-run" in raw_args and not (raw_args and raw_args[0].startswith("sidecars")):
        return _run_lightweight_dry_run(raw_args)
    from .cli import main as cli_main

    return cli_main(raw_args)

if __name__ == "__main__":
    raise SystemExit(main())
