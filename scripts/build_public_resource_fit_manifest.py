#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _resource(
    *,
    id: str,
    name: str,
    resource_type: str,
    modality: str,
    primary_url: str,
    secondary_urls: list[str],
    license_or_access_notes: str,
    current_access_status: str,
    fit_score_1_to_10: int,
    why_fit: str,
    why_not_score_1_to_10: int,
    why_not: str,
    best_use_in_signal_engine: str,
    recommended_phase: str,
    implementation_effort: str,
    risk_level: str,
    default_path: str,
    notes: str,
) -> dict[str, object]:
    return {
        "id": id,
        "name": name,
        "resource_type": resource_type,
        "modality": modality,
        "primary_url": primary_url,
        "secondary_urls": secondary_urls,
        "license_or_access_notes": license_or_access_notes,
        "current_access_status": current_access_status,
        "fit_score_1_to_10": fit_score_1_to_10,
        "why_fit": why_fit,
        "why_not_score_1_to_10": why_not_score_1_to_10,
        "why_not": why_not,
        "best_use_in_signal_engine": best_use_in_signal_engine,
        "recommended_phase": recommended_phase,
        "implementation_effort": implementation_effort,
        "risk_level": risk_level,
        "default_path": default_path,
        "notes": notes,
    }


PUBLIC_RESOURCES: tuple[dict[str, object], ...] = (
    _resource(
        id="loughran_mcdonald_dictionary",
        name="Loughran-McDonald Master Dictionary",
        resource_type="dictionary",
        modality="transcript",
        primary_url="https://sraf.nd.edu/loughranmcdonald-master-dictionary/",
        secondary_urls=[
            "https://www3.nd.edu/~mcdonald/Word_Lists_files/Documentation_MasterandDocumentDictionaries.pdf",
            "https://ssrn.com/abstract=1331573",
        ],
        license_or_access_notes="Official Notre Dame academic distribution is public; review terms before vendoring dictionary files.",
        current_access_status="available",
        fit_score_1_to_10=9,
        why_fit="Best fit for deterministic finance-language extension, especially uncertainty, modal strength, and constraint cues that can stay auditable.",
        why_not_score_1_to_10=3,
        why_not="Dictionary counts still need conversational context and do not solve dialogue structure or multi-domain review on their own.",
        best_use_in_signal_engine="Extend canonical deterministic finance lexicons and benchmark transcript-only feature coverage.",
        recommended_phase="now",
        implementation_effort="low",
        risk_level="low",
        default_path="canonical",
        notes="Strongest immediate fit for earnings-call terminology without adding model dependencies.",
    ),
    _resource(
        id="financial_phrasebank",
        name="Financial PhraseBank",
        resource_type="dataset",
        modality="transcript",
        primary_url="https://arxiv.org/abs/1307.5336",
        secondary_urls=[
            "https://huggingface.co/datasets/ArtGarfunkel/FinancialPhraseBank",
            "https://doi.org/10.48550/arXiv.1307.5336",
        ],
        license_or_access_notes="Original paper is public; mirrors often expose separate dataset terms, so reuse should be re-checked before local benchmarking.",
        current_access_status="needs_verification",
        fit_score_1_to_10=7,
        why_fit="Useful small finance benchmark for sanity-checking sentiment behavior on short financial text.",
        why_not_score_1_to_10=5,
        why_not="Short headline sentiment does not map cleanly to transcript evidence, analyst pressure, or reviewer actionability.",
        best_use_in_signal_engine="Benchmark-only transcript sanity checks for finance sentiment, not canonical scoring.",
        recommended_phase="next",
        implementation_effort="medium",
        risk_level="medium",
        default_path="benchmark_only",
        notes="Helpful evaluation reference, but weaker fit than transcript-specific lexicon work.",
    ),
    _resource(
        id="switchboard_mrda",
        name="Switchboard Dialog Act Corpus / MRDA",
        resource_type="corpus",
        modality="transcript_audio",
        primary_url="https://catalog.ldc.upenn.edu/LDC97S62",
        secondary_urls=[
            "https://aclanthology.org/W04-2319.pdf",
            "https://compprag.christopherpotts.net/swda.html",
        ],
        license_or_access_notes="Core corpora are gated through LDC or research distribution; metadata and papers are accessible.",
        current_access_status="gated",
        fit_score_1_to_10=6,
        why_fit="Strong conceptual fit for question-answer structure, interruptions, and conversational move taxonomies.",
        why_not_score_1_to_10=6,
        why_not="Access is gated and the domains are not earnings, support, or sales, so direct adoption would add friction.",
        best_use_in_signal_engine="Dialogue-act taxonomy reference and later benchmark-only experiments if access becomes available.",
        recommended_phase="next",
        implementation_effort="medium",
        risk_level="medium",
        default_path="benchmark_only",
        notes="Good methodology reference, but not a default-path dependency.",
    ),
    _resource(
        id="finbert",
        name="FinBERT",
        resource_type="model",
        modality="transcript",
        primary_url="https://huggingface.co/ProsusAI/finbert",
        secondary_urls=[
            "https://arxiv.org/abs/1908.10063",
            "https://huggingface.co/papers/1908.10063",
        ],
        license_or_access_notes="Model card is public; downstream commercial and data-provenance review is still advisable before broader use.",
        current_access_status="available",
        fit_score_1_to_10=6,
        why_fit="Good optional finance-domain comparison point for transcript sentiment benchmarking.",
        why_not_score_1_to_10=7,
        why_not="Black-box sentiment scores are too narrow and too opaque to become canonical signal extraction in this repo.",
        best_use_in_signal_engine="Optional benchmark-only comparator for finance text, especially earnings-call phrasing.",
        recommended_phase="later",
        implementation_effort="medium",
        risk_level="medium",
        default_path="benchmark_only",
        notes="Useful as a measured comparator, not as product truth.",
    ),
    _resource(
        id="opensmile",
        name="openSMILE",
        resource_type="tool",
        modality="audio",
        primary_url="https://www.audeering.com/research/opensmile/",
        secondary_urls=[
            "https://audeering.github.io/opensmile/",
            "https://pypi.org/project/opensmile/",
        ],
        license_or_access_notes="audEERING documents research-oriented usage; commercial usage requires care.",
        current_access_status="available",
        fit_score_1_to_10=5,
        why_fit="Strong bounded fit for pauses, energy, and prosodic review cues without claiming hidden-state inference.",
        why_not_score_1_to_10=7,
        why_not="Audio features add dependency and rights complexity and should not be interpreted as internal-state truth.",
        best_use_in_signal_engine="Optional audio adapter for sparse prosody cues in later pilot cases.",
        recommended_phase="later",
        implementation_effort="medium",
        risk_level="medium",
        default_path="optional_adapter",
        notes="Only useful once aligned approved audio exists.",
    ),
    _resource(
        id="opencv",
        name="OpenCV",
        resource_type="library",
        modality="video",
        primary_url="https://opencv.org/",
        secondary_urls=[
            "https://docs.opencv.org/master/index.html",
            "https://opencv.org/license/",
        ],
        license_or_access_notes="OpenCV 4.5.0+ is Apache 2.0; older versions are BSD-licensed.",
        current_access_status="available",
        fit_score_1_to_10=4,
        why_fit="Lightweight fit for frame stats, motion proxies, and simple video preprocessing if sparse visual review is added later.",
        why_not_score_1_to_10=8,
        why_not="Basic vision utilities do not justify body-language certainty claims and are far from canonical transcript evaluation.",
        best_use_in_signal_engine="Optional video utility layer for later sparse cue extraction only.",
        recommended_phase="later",
        implementation_effort="low",
        risk_level="medium",
        default_path="optional_adapter",
        notes="Best treated as infrastructure, not as inference evidence on its own.",
    ),
    _resource(
        id="meld",
        name="MELD",
        resource_type="dataset",
        modality="multimodal",
        primary_url="https://affective-meld.github.io/",
        secondary_urls=[
            "https://arxiv.org/abs/1810.02508",
            "https://github.com/declare-lab/MELD",
        ],
        license_or_access_notes="Public project resources exist, but media provenance and downstream reuse posture should be treated carefully.",
        current_access_status="available",
        fit_score_1_to_10=4,
        why_fit="Useful research reference for multimodal conversation emotion benchmarks and evaluation language.",
        why_not_score_1_to_10=8,
        why_not="Friends-based emotion labels are a weak fit for enterprise transcript review and recruiter-facing proof.",
        best_use_in_signal_engine="Benchmark framing only for future multimodal comparisons, not core pipeline work.",
        recommended_phase="later",
        implementation_effort="high",
        risk_level="high",
        default_path="benchmark_only",
        notes="Keep this in documentation until aligned business-conversation media exists.",
    ),
    _resource(
        id="cmu_mosei",
        name="CMU-MOSEI",
        resource_type="dataset",
        modality="multimodal",
        primary_url="https://github.com/CMU-MultiComp-Lab/CMU-MultimodalSDK",
        secondary_urls=[
            "https://audeering.github.io/datasets/datasets/cmu-mosei.html",
            "https://github.com/CMU-MultiComp-Lab/CMU-MultimodalSDK",
        ],
        license_or_access_notes="Widely cited research benchmark, but current practical access/download path should be re-verified before use.",
        current_access_status="needs_verification",
        fit_score_1_to_10=3,
        why_fit="Only useful as a broad multimodal sentiment benchmark reference.",
        why_not_score_1_to_10=9,
        why_not="Generic multimodal sentiment/emotion is a poor fit for transcript-first, evidence-backed business signal extraction.",
        best_use_in_signal_engine="Documentation-only cautionary reference for later multimodal benchmarking decisions.",
        recommended_phase="avoid_for_now",
        implementation_effort="high",
        risk_level="high",
        default_path="documentation_only",
        notes="Low portfolio fit for the current repo direction.",
    ),
)


def _sorted_resources() -> list[dict[str, object]]:
    return sorted(
        PUBLIC_RESOURCES,
        key=lambda row: (
            -int(row["fit_score_1_to_10"]),
            int(row["why_not_score_1_to_10"]),
            str(row["name"]),
        ),
    )


def _render_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Public Resource Fit Report",
        "",
        "This report ranks public resources for Signal Engine 2.0 using conservative fit and risk scores.",
        "It is a planning aid, not a claim that these resources should become canonical or default dependencies.",
        "",
        "## Ranking Table",
        "",
        "| rank | resource | fit | why-not | phase | path | access |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"| {index} | {row['name']} | {row['fit_score_1_to_10']} | {row['why_not_score_1_to_10']} | {row['recommended_phase']} | {row['default_path']} | {row['current_access_status']} |"
        )
    lines.extend(["", "## Detailed Notes", ""])
    for row in rows:
        lines.extend(
            [
                f"### {row['name']}",
                "",
                f"- primary_url: [{row['primary_url']}]({row['primary_url']})",
                f"- resource_type / modality: `{row['resource_type']}` / `{row['modality']}`",
                f"- fit / why-not: `{row['fit_score_1_to_10']}` / `{row['why_not_score_1_to_10']}`",
                f"- recommended_phase: `{row['recommended_phase']}`",
                f"- default_path: `{row['default_path']}`",
                f"- implementation_effort: `{row['implementation_effort']}`",
                f"- risk_level: `{row['risk_level']}`",
                f"- access: {row['current_access_status']}",
                f"- license_or_access_notes: {row['license_or_access_notes']}",
                f"- best_use_in_signal_engine: {row['best_use_in_signal_engine']}",
                f"- why_fit: {row['why_fit']}",
                f"- why_not: {row['why_not']}",
                f"- notes: {row['notes']}",
                "",
            ]
        )
    lines.extend(
        [
            "## What Not To Do",
            "",
            "- Do not make FinBERT, MELD, or CMU-MOSEI canonical for this repo on the basis of this report alone.",
            "- Do not turn openSMILE or OpenCV features into truth claims about hidden emotion, deception, or intent.",
            "- Do not assume public mirrors are commercially clean without re-checking dataset or model terms.",
            "- Do not make gated corpora like Switchboard or MRDA part of default CI or setup requirements.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the public resource fit manifest and Markdown report.")
    parser.add_argument(
        "--manifest-out",
        default=str(ROOT / "data" / "research_resource_fit" / "public_resource_fit_manifest.json"),
        help="Path to the JSON manifest output.",
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "public-resource-fit-report.md"),
        help="Path to the Markdown report output.",
    )
    args = parser.parse_args(argv)

    rows = _sorted_resources()
    manifest = {
        "status": "ok",
        "generated_at": datetime.now(UTC).isoformat(),
        "resource_count": len(rows),
        "resources": rows,
    }

    manifest_path = Path(args.manifest_out)
    report_path = Path(args.report_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path.write_text(_render_markdown(rows), encoding="utf-8")

    print(json.dumps({"status": "ok", "resource_count": len(rows), "manifest_path": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
