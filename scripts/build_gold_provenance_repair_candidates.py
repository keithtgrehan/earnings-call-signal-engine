#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _evidence_text(row: dict[str, Any]) -> str:
    for field in ("evidence_text", "text", "redacted_preview"):
        value = str(row.get(field, "") or "").strip()
        if value:
            return value
    metadata = row.get("metadata", {})
    if isinstance(metadata, dict):
        return str(metadata.get("evidence_text", "") or "").strip()
    return ""


def _is_external_or_weak(row: dict[str, Any]) -> bool:
    label_source = str(row.get("label_source", "")).lower()
    source_file = str(row.get("source_file", "")).lower()
    source_type = str(row.get("source_type", "")).lower()
    markers = ("external", "weak", "financial_phrasebank", "loughran", "benchmark")
    return any(marker in label_source or marker in source_file or marker in source_type for marker in markers)


def _registry_indexes(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_case: dict[str, dict[str, Any]] = {}
    by_source_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        if str(row.get("media_type", "transcript")) != "transcript":
            continue
        case_id = str(row.get("case_id", "")).strip()
        if case_id and case_id not in by_case:
            by_case[case_id] = row
        source_path = str(row.get("source_path_ref", "")).strip()
        if source_path:
            by_source_name[Path(source_path).name.lower()] = row
            by_source_name[Path(source_path).stem.lower()] = row
    return by_case, by_source_name


def _match_registry(row: dict[str, Any], by_case: dict[str, dict[str, Any]], by_source_name: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    case_id = str(row.get("case_id", "")).strip()
    if case_id in by_case:
        return by_case[case_id]
    source_file = str(row.get("source_file", "")).strip()
    if source_file:
        name = Path(source_file).name.lower()
        stem = Path(source_file).stem.lower()
        return by_source_name.get(name) or by_source_name.get(stem)
    return None


def _classify_row(
    row: dict[str, Any],
    registry_match: dict[str, Any] | None,
    evidence: str,
    duplicate: bool,
) -> str:
    if duplicate:
        return "blocked_duplicate"
    if not evidence:
        return "blocked_missing_evidence"
    if _is_external_or_weak(row):
        return "blocked_external_or_weak_source"
    if registry_match:
        return "repairable_with_registered_source"
    if str(row.get("provenance_hash", "")).startswith("sha256:"):
        return "repairable_schema_only"
    return "needs_manual_source_mapping"


def build_repair_candidates(*, gold_path: Path, registry_path: Path, audit_dir: Path | None = None) -> list[dict[str, Any]]:
    gold_rows = _load_jsonl(gold_path)
    registry_rows = _load_jsonl(registry_path)
    by_case, by_source_name = _registry_indexes(registry_rows)
    seen_keys: set[tuple[str, str, str]] = set()
    candidates: list[dict[str, Any]] = []
    for row in gold_rows:
        evidence = _evidence_text(row)
        duplicate_key = (str(row.get("case_id", "")), str(row.get("source_file", "")), evidence)
        duplicate = duplicate_key in seen_keys
        seen_keys.add(duplicate_key)
        registry_match = _match_registry(row, by_case, by_source_name)
        status = _classify_row(row, registry_match, evidence, duplicate)
        candidate: dict[str, Any] = {
            "candidate_id": row.get("candidate_id") or row.get("id", ""),
            "case_id": row.get("case_id", ""),
            "source_file": row.get("source_file", ""),
            "label_source": row.get("label_source", ""),
            "repair_status": status,
            "evidence_text": evidence,
            "evidence_text_hash": _stable_hash({"evidence_text": evidence}) if evidence else "",
            "canonical_gold_edited": False,
            "manual_action_required": "",
        }
        if registry_match and status == "repairable_with_registered_source":
            candidate["registered_source_path_ref"] = registry_match.get("source_path_ref", "")
            candidate["proposed_source_sha256"] = registry_match.get("source_sha256", "")
            candidate["proposed_provenance_hash"] = _stable_hash(
                {
                    "candidate_id": candidate["candidate_id"],
                    "case_id": candidate["case_id"],
                    "evidence_text_hash": candidate["evidence_text_hash"],
                    "source_sha256": candidate["proposed_source_sha256"],
                }
            )
        elif status == "needs_manual_source_mapping":
            candidate["manual_action_required"] = "Map this legacy gold row to a registered manual-local transcript path/hash."
        elif status == "repairable_schema_only":
            candidate["manual_action_required"] = "Schema repair may be possible, but source hash still requires manual verification."
        elif status == "blocked_missing_evidence":
            candidate["manual_action_required"] = "Evidence text is missing; do not invent evidence."
        elif status == "blocked_external_or_weak_source":
            candidate["manual_action_required"] = "External or weak-label sources cannot become Signal Engine gold automatically."
        elif status == "blocked_duplicate":
            candidate["manual_action_required"] = "Duplicate evidence/source key requires human adjudication."
        candidates.append(candidate)

    if audit_dir and audit_dir.exists():
        # The audit directory is optional context; canonical gold remains read-only.
        candidate_ids = {str(row.get("candidate_id", "")) for row in candidates}
        for audit_file in sorted(audit_dir.glob("*.jsonl")):
            for audit_row in _load_jsonl(audit_file):
                candidate_id = str(audit_row.get("candidate_id", ""))
                if candidate_id not in candidate_ids:
                    continue
                for candidate in candidates:
                    if str(candidate.get("candidate_id")) == candidate_id:
                        candidate.setdefault("audit_reasons", audit_row.get("audit_reasons", []))
                        candidate.setdefault("audit_status", audit_row.get("audit_status", ""))
    return candidates


def _write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    counts = Counter(str(row.get("repair_status", "unknown")) for row in rows)
    lines = [
        "# Gold Provenance Repair Candidates",
        "",
        f"- Candidate rows: `{len(rows)}`",
        "- Canonical gold edited: `false`",
        "- Evidence invented: `false`",
        "",
        "## Status Counts",
        "",
    ]
    lines.extend(f"- `{status}`: `{count}`" for status, count in sorted(counts.items()))
    lines.extend(["", "## Next Step", "", "Review repairable rows in staging, map unresolved rows to registered source path/hash, then adjudicate before promotion."])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build staging candidates for repairing legacy gold provenance without editing canonical gold.")
    parser.add_argument("--gold", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--audit-dir", default="reports/gold_label_audit")
    parser.add_argument("--out", default="data/review/staging/gold_provenance_repair_candidates.jsonl")
    parser.add_argument("--report", default="reports/gold_provenance_repair_candidates.md")
    args = parser.parse_args(argv)
    rows = build_repair_candidates(gold_path=Path(args.gold), registry_path=Path(args.registry), audit_dir=Path(args.audit_dir))
    _write_jsonl(Path(args.out), rows)
    _write_report(Path(args.report), rows)
    print(f"Gold provenance repair candidates written: {len(rows)} row(s), canonical gold unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
