#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.ir_sec_acquisition import write_text


def build_report_text() -> str:
    return """# Manual-Local vs IR/SEC Discovery Gap

## What Method 1 / Manual-Local Gives

- actual transcript body already in local control
- sha256 hash provenance
- explicit operator-supplied path
- easier repeatable parsing
- no live source volatility
- no robots/source-term ambiguity at runtime
- no reliance on candidate URLs
- human-confirmed event identity
- direct linkage to reviewed labels

## What IR/SEC Discovery Adds

- source candidates at scale
- event identity metadata
- 8-K/press release/filing context
- official IR availability indicators
- asset availability map
- blocked/manual-action queue
- 500-call universe status

## Practical Conclusion

Official IR and SEC/EDGAR metadata discovery is useful for coverage planning and provenance triage. It cannot guarantee transcript bodies, transcript quality, or reuse permission. When source terms are unclear, manual-local registration remains the fastest fully controlled path because files are represented by operator path plus sha256 hash only.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report the manual-local versus IR/SEC discovery gap.")
    parser.add_argument("--out", default="reports/agent5/manual_local_vs_ir_sec_gap.md")
    args = parser.parse_args(argv)
    write_text(ROOT / args.out, build_report_text())
    print(f"Manual-local versus IR/SEC gap report written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
