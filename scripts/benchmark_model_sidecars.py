#!/usr/bin/env python3
"""Benchmark optional model-sidecar runtime behavior for one or more processed cases."""

from __future__ import annotations

import sys

from earnings_call_sentiment import cli


def main() -> int:
    return cli.main(["sidecars-benchmark", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
