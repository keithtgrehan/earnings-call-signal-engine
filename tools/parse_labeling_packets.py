#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import parse_packet, write_csv, write_jsonl  # noqa: E402

CANDIDATE_FIELDS = [
    "candidate_id",
    "source",
    "source_row",
    "case_id",
    "weak_label",
    "confidence",
    "reason",
    "text",
    "noise_flag",
    "duplicate_of",
]


def write_inventory(packet: Path, candidates: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    root = ROOT
    label_counts = Counter(str(row.get("weak_label") or "") for row in candidates)
    noise_counts = Counter(str(row.get("noise_flag") or "clean") or "clean" for row in candidates)
    duplicate_count = sum(1 for row in candidates if row.get("duplicate_of"))
    data_files = [path for path in sorted((root / "data").rglob("*")) if path.is_file()]
    packet_files = [path for path in data_files if "packet" in path.name.lower() or path.suffix.lower() == ".zip"]
    candidate_files = [path for path in data_files if "candidate" in path.name.lower()]
    weak_label_files = [path for path in data_files if "weak" in path.name.lower() and "label" in path.name.lower()]
    gold_label_files = [path for path in data_files if "gold" in str(path).lower() or "labels" in path.name.lower()]
    corpus_dirs = [path for path in sorted((root / "data").rglob("*")) if path.is_dir() and "corpus" in str(path).lower()]
    lines = [
        "# Labeling Data Inventory",
        "",
        f"- packet: `{packet}`",
        f"- candidates: `{len(candidates)}`",
        f"- duplicates_flagged: `{duplicate_count}`",
        f"- labeling_packet_files_found: `{len(packet_files)}`",
        f"- candidate_files_found: `{len(candidate_files)}`",
        f"- weak_label_files_found: `{len(weak_label_files)}`",
        f"- gold_or_label_files_found: `{len(gold_label_files)}`",
        f"- corpus_directories_found: `{len(corpus_dirs)}`",
        "",
        "## Candidate Sources",
        "",
    ]
    source_counts = Counter(str(row.get("source") or "") for row in candidates)
    for source, count in sorted(source_counts.items()):
        lines.append(f"- `{source}`: {count}")
    lines.extend(["", "## Weak Label Counts", ""])
    for label, count in sorted(label_counts.items()):
        lines.append(f"- `{label or 'missing'}`: {count}")
    lines.extend(["", "## Noise Flags", ""])
    for flag, count in sorted(noise_counts.items()):
        lines.append(f"- `{flag}`: {count}")
    for title, paths in [
        ("Labeling Packets", packet_files),
        ("Candidate Files", candidate_files),
        ("Weak Label Files", weak_label_files),
        ("Gold Or Label Files", gold_label_files),
        ("Corpus Directories", corpus_dirs),
    ]:
        lines.extend(["", f"## {title}", ""])
        if not paths:
            lines.append("- none found")
            continue
        for path in paths[:80]:
            lines.append(f"- `{path.relative_to(root)}`")
        if len(paths) > 80:
            lines.append(f"- ... {len(paths) - 80} more")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse labeling packets into normalized candidate JSONL/CSV.")
    parser.add_argument("--packet", required=True, help="Packet file, directory, or safe zip archive.")
    parser.add_argument("--jsonl-out", default=str(ROOT / "data" / "labeling" / "candidates.jsonl"))
    parser.add_argument("--csv-out", default=str(ROOT / "data" / "labeling" / "candidates.csv"))
    parser.add_argument("--inventory-out", default=str(ROOT / "docs" / "labeling" / "data_inventory.md"))
    args = parser.parse_args(argv)

    packet = Path(args.packet)
    if not packet.exists():
        raise SystemExit(f"packet not found: {packet}")
    candidates = parse_packet(packet)
    write_jsonl(Path(args.jsonl_out), candidates)
    write_csv(Path(args.csv_out), candidates, CANDIDATE_FIELDS)
    write_inventory(packet, candidates, Path(args.inventory_out))
    print(f"parsed {len(candidates)} candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
