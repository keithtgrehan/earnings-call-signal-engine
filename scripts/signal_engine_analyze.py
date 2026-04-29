#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.domains import SUPPORTED_DOMAINS
from signal_engine.pipeline import _load_records, analyze_conversation_record
from signal_engine.privacy import redact_conversation, summarize_redactions


def _analyze_records(
    input_path: str | Path,
    *,
    domain: str,
    redact_pii: bool,
) -> list[dict]:
    results: list[dict] = []
    for record in _load_records(Path(input_path)):
        record_for_analysis = record
        redaction_summary: dict | None = None
        if redact_pii:
            redacted = redact_conversation(record)
            record_for_analysis = redacted["conversation"]
            redaction_summary = summarize_redactions(redacted["redactions"])
        result = analyze_conversation_record(record_for_analysis, domain=domain)
        if redaction_summary is not None:
            result["metadata"]["pii_redaction"] = {
                "enabled": True,
                "summary": redaction_summary,
            }
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic Signal Engine 2.0 analysis on a transcript JSON or JSONL file."
    )
    parser.add_argument("input_path", help="Path to a JSON or JSONL transcript file.")
    parser.add_argument(
        "--domain",
        required=True,
        choices=SUPPORTED_DOMAINS,
        help="Conversation domain to analyze.",
    )
    parser.add_argument(
        "--conversation-id",
        help="Optional conversation id to select when the input file contains multiple records.",
    )
    parser.add_argument(
        "--redact-pii",
        action="store_true",
        help="Apply deterministic fallback PII redaction before analysis.",
    )
    args = parser.parse_args(argv)

    results = _analyze_records(
        args.input_path,
        domain=args.domain,
        redact_pii=args.redact_pii,
    )
    if not results:
        raise RuntimeError("No analyzable conversations found.")

    if args.conversation_id:
        matches = [item for item in results if item["conversation_id"] == args.conversation_id]
        if not matches:
            raise RuntimeError(f"Conversation id not found: {args.conversation_id}")
        payload = matches[0]
    else:
        payload = results[0]

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
