#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.storage.sqlite_store import init_db, table_names  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize the local Signal Engine SQLite operational store.")
    parser.add_argument("--db-path", default=str(ROOT / "data" / "review" / "signal_engine.db"))
    args = parser.parse_args(argv)
    connection = init_db(Path(args.db_path))
    tables = sorted(table_names(connection))
    connection.close()
    print(json.dumps({"db_path": args.db_path, "tables": tables}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
