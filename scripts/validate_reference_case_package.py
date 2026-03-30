#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from earnings_call_sentiment.reference_case_standard import validate_reference_case_package


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that a bounded reviewer/demo case package meets the reference-case artifact and caveat standard."
    )
    parser.add_argument("--package-dir", required=True, help="Directory containing the persistent reviewed case package.")
    parser.add_argument("--prefix", required=True, help="Case-specific filename prefix, for example `meta` or `netflix`.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_dir = Path(args.package_dir).expanduser().resolve()
    errors = validate_reference_case_package(package_dir, args.prefix)
    payload = {
        "package_dir": str(package_dir),
        "prefix": str(args.prefix),
        "valid": not errors,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
