#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from textwrap import fill

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "research" / "ilya_reading_list"
DOC_DIR = ROOT / "docs" / "research" / "ilya_reading_list"
PAPERS_DIR = DOC_DIR / "papers"

FILENAME_MAP = {
    "first_law_complexodynamics": "01_first_law_complexodynamics.md",
    "unreasonable_effectiveness_rnns": "02_unreasonable_effectiveness_rnns.md",
    "understanding_lstm_networks": "03_understanding_lstm_networks.md",
    "rnn_regularization": "04_rnn_regularization.md",
    "keeping_neural_networks_simple_mdl_weights": "05_keeping_neural_networks_simple_mdl_weights.md",
    "pointer_networks": "06_pointer_networks.md",
    "imagenet_classification_deep_cnn": "07_imagenet_classification_deep_cnn.md",
    "order_matters_seq2seq_sets": "08_order_matters_seq2seq_sets.md",
    "gpipe_scaling_microbatch_pipeline_parallelism": "09_gpipe_scaling_microbatch_pipeline_parallelism.md",
    "deep_residual_learning_image_recognition": "10_deep_residual_learning_image_recognition.md",
    "multi_scale_context_aggregation_dilated_convolutions": "11_multi_scale_context_aggregation_dilated_convolutions.md",
    "neural_message_passing_quantum_chemistry": "12_neural_message_passing_quantum_chemistry.md",
    "attention_is_all_you_need": "13_attention_is_all_you_need.md",
    "nmt_jointly_learning_align_translate": "14_nmt_jointly_learning_align_translate.md",
    "identity_mappings_deep_residual_networks": "15_identity_mappings_deep_residual_networks.md",
    "simple_module_relational_reasoning": "16_simple_module_relational_reasoning.md",
    "variational_lossy_autoencoder": "17_variational_lossy_autoencoder.md",
    "relational_recurrent_neural_networks": "18_relational_recurrent_neural_networks.md",
    "coffee_automaton_complexity_closed_systems": "19_coffee_automaton_complexity_closed_systems.md",
    "neural_turing_machines": "20_neural_turing_machines.md",
    "deep_speech_2_end_to_end_speech_recognition": "21_deep_speech_2_end_to_end_speech_recognition.md",
    "scaling_laws_neural_language_models": "22_scaling_laws_neural_language_models.md",
    "tutorial_minimum_description_length_principle": "23_tutorial_minimum_description_length_principle.md",
    "machine_super_intelligence": "24_machine_super_intelligence.md",
    "kolmogorov_complexity_algorithmic_randomness": "25_kolmogorov_complexity_algorithmic_randomness.md",
    "stanford_cs231n_convolutional_neural_networks": "26_cs231n.md",
}


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _wrapped(text: str) -> str:
    return fill(" ".join(text.split()), width=100)


def _brief(paper: dict, registry: dict, extracted: dict) -> str:
    source_url = registry.get("canonical_url") or registry.get("pdf_url") or registry.get("html_url")
    feature_ideas = paper.get("future_features", [])
    while len(feature_ideas) < 5:
        feature_ideas.append(f"{paper['category']} evaluation note for reviewer-facing Signal Engine workflows")
    executive = _wrapped(
        f"{paper['title']} is included here as a research asset for Signal Engine 2.0, not as an implemented model. "
        f"The core idea is: {paper.get('core_idea', '')} Historically, {paper.get('historical_importance', '')} "
        f"For the earnings-call project, the practical value is to translate this idea into evidence-first transcript "
        f"workflows, safer retrieval, clearer model-selection gates, and explicit limits on what the system claims. "
        f"The parsed source status is {registry.get('parse_status')}; raw source text was processed locally when available "
        f"but not committed because redistribution rights differ by publisher and author site. The useful engineering lesson "
        f"is to preserve deterministic behavior, add optional research sidecars only behind evaluation gates, and require "
        f"source evidence for every signal that might affect an analyst or portfolio-review narrative."
    )
    backlog_now = [
        "Add a research note or deterministic diagnostic that can run on existing transcript artifacts.",
        "Use the idea to improve evidence-span review, weak-label audits, or retrieval evaluation.",
    ]
    backlog_later = [
        "Promote to optional local model or reranker experiments only after stable held-out labels exist.",
        "Measure lift over deterministic baselines with reviewer-facing error analysis.",
    ]
    backlog_avoid = [
        "Do not claim neural implementation from this research brief alone.",
        "Do not replace the deterministic engine with an opaque model before evaluation gates are met.",
    ]
    method = _wrapped(
        f"Mechanically, this source belongs to `{paper['category']}` and centers on {', '.join(paper.get('core_concepts', [])[:5])}. "
        f"In Signal Engine terms, the method should be treated as a design pattern: identify the data object, preserve provenance, "
        f"define the transformation, and test whether it improves evidence quality, not just model elegance."
    )
    relevance = [
        "transcript sectioning: use the paper to decide whether chronology, sections, or context windows matter for a signal.",
        "speaker-turn modeling: apply the lesson to management/analyst role structure only when labels support it.",
        "evidence span extraction: prefer citation-first outputs and measure whether the system points to the right text.",
        "sentiment/emotion/intent scoring: use as a candidate sidecar idea, never as proof of validated sentiment lift.",
        "weak labeling: convert the research idea into auditable rule checks before using it to generate labels.",
        "active learning: prioritize uncertain or high-signal-density transcript spans for human review.",
        "multimodal audio/video roadmap: treat media features as residual evidence over transcripts unless media labels exist.",
        "RAG/retrieval: evaluate recall, citation precision, and usefulness before adding heavier retrieval infrastructure.",
        "evaluation: define an ablation and a failure mode before any implementation work starts.",
    ]
    return f"""# {paper['title']}

## Status

- Source status: {registry.get('source_type')}
- Parse status: {registry.get('parse_status')}
- Confidence: {registry.get('source_confidence')}
- Source URL: {source_url}

## Executive Summary

{executive}

## Core Technical Idea

{_wrapped(paper.get('core_idea', ''))}

## Key Concepts

{_bullets([f'{term}: research concept relevant to {paper["category"]}.' for term in paper.get('core_concepts', [])])}

## Architecture / Method

{method}

Detected source sections: {', '.join(extracted.get('sections_detected', []) or ['not detected'])}. Parsed text length recorded locally: {extracted.get('text_length_chars', 0)} characters.

## Why It Mattered

{_wrapped(paper.get('historical_importance', ''))}

## What To Learn From It

{_wrapped(paper.get('beginner_takeaway', ''))}

## Signal Engine 2.0 Relevance

{_bullets(relevance)}

## Direct Feature Ideas

{_bullets(feature_ideas[:5])}

## Implementation Backlog

### now

{_bullets(backlog_now)}

### later

{_bullets(backlog_later)}

### avoid_for_now

{_bullets(backlog_avoid)}

## Risks / Limitations

{_bullets(paper.get('risks_limitations', []))}

## Practical Takeaway

{_wrapped('Keith should remember this paper as a source of design pressure, not a shortcut. The project value comes from turning the research lesson into small, testable Signal Engine assets: explicit evidence, clear labels, source-grounded retrieval, and honest claims about what has and has not been implemented.')}
"""


def _write_feature_backlog(metadata: list[dict]) -> None:
    rows = []
    for paper in metadata:
        for index, feature in enumerate(paper.get("future_features", [])[:3], start=1):
            rows.append(
                {
                    "feature_id": f"{paper['id']}_feature_{index}",
                    "feature_name": feature,
                    "source_paper_ids": paper["id"],
                    "signal_engine_area": paper["category"],
                    "description": f"Research-derived candidate feature from {paper['title']}: {feature}.",
                    "implementation_stage": "now" if index == 1 and paper["category"] in {"attention_transformers", "sequence_models", "evaluation_theory", "compression_mdl_complexity"} else "later",
                    "complexity": "low" if paper["category"] in {"evaluation_theory", "compression_mdl_complexity"} else "medium",
                    "expected_value": "high" if paper["category"] in {"attention_transformers", "evaluation_theory", "sequence_models"} else "medium",
                    "dependency": "stable evidence-span labels and deterministic baseline outputs",
                    "evaluation_method": "; ".join(paper.get("possible_evaluation_ideas", [])[:2]),
                }
            )
    path = DATA_DIR / "signal_engine_feature_backlog.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_synthesis(metadata: list[dict], registry_by_id: dict[str, dict]) -> None:
    parsed = [paper["id"] for paper in metadata if registry_by_id[paper["id"]].get("parse_status") == "full_text_parsed"]
    text = f"""# Signal Engine 2.0 Full Research Synthesis

## 1. What These Papers Collectively Teach

The list is not a single architecture prescription. It teaches a progression: simple description-length thinking, sequence memory, attention and pointers, residual/additive design, graph and relational structure, speech/vision foundations, and scaling discipline. The strongest shared lesson for Signal Engine 2.0 is that intelligence should be made observable through evidence, ablations, and staged evaluation.

## 2. What Is Immediately Useful For Signal Engine

- Evidence-first retrieval inspired by attention and pointer mechanisms.
- Transcript sectioning and callback tracking inspired by RNN/LSTM memory.
- Simplicity and weak-label governance from MDL and regularization papers.
- Residual sidecar design that preserves deterministic outputs.
- Reviewer-facing validation metrics before production ML claims.

## 3. What Is Useful Only After 100+ Labeled Transcripts

- Optional transformer or embedding reranker baselines.
- Learned sequence classifiers for uncertainty, friction, and guidance shifts.
- Active-learning loops trained on disagreement and false-positive patterns.
- Learning curves that compare feature complexity against held-out-call performance.

## 4. What Is Useful Only After Multimodal Assets Exist

- Deep Speech-style ASR quality gates and audio provenance tracking.
- Prosody and pause features joined to transcript spans.
- Video/visual sidecars evaluated as incremental lift over text.
- Speaker relation graphs that include audio/video timing only when legally safe media exists.

## 5. What Should Be Avoided

- Training large models before data volume and labels justify it.
- Treating attention weights as explanations without evidence-span validation.
- Committing raw PDFs or raw extracted source text without clear redistribution rights.
- Replacing deterministic Signal Engine behavior with a black-box model.
- Claiming market prediction or production-grade multimodal intelligence.

## 6. Feature Backlog

See `data/research/ilya_reading_list/signal_engine_feature_backlog.csv`. The backlog converts each paper into staged features with expected value, dependencies, and evaluation methods.

## 7. Evaluation Backlog

- Evidence-span precision/recall.
- Retrieval recall@k plus citation precision.
- Reviewer time-to-evidence.
- Weak-label false-positive reduction.
- Learning curves at 30, 100, and 500 transcripts.
- Text-only versus text+audio/video ablations after multimodal assets exist.

## 8. Dataset / Labeling Implications

The papers collectively argue for more careful labels, not more dramatic models. At 30 transcripts, stabilize taxonomy and evidence spans. At 100 transcripts, introduce held-out model baselines. At 500 transcripts, compare model families and relation/multimodal sidecars with credible ablations.

## 9. Architecture Implications

Signal Engine should remain a deterministic-first pipeline with optional sidecars: source registry, transcript memory, evidence pointer layer, retrieval memory, speaker relation graph, and evaluation dashboard. The raw transcript remains the source of truth.

## 10. Hiring / Portfolio Narrative

This asset shows research taste and product discipline: it connects landmark AI ideas to a concrete business NLP system while refusing to overclaim. It says: Keith can read frontier research, extract practical architecture choices, and keep evidence and evaluation ahead of hype.

## Parse Coverage

- Full text parsed locally: {len(parsed)} papers.
- Non-full-text statuses are retained explicitly in `source_registry.json`.
"""
    (DOC_DIR / "signal_engine_2_0_full_synthesis.md").write_text(text, encoding="utf-8")


def _write_reading_plan(metadata: list[dict]) -> None:
    fast = [
        "tutorial_minimum_description_length_principle",
        "understanding_lstm_networks",
        "rnn_regularization",
        "nmt_jointly_learning_align_translate",
        "pointer_networks",
        "attention_is_all_you_need",
        "scaling_laws_neural_language_models",
        "deep_speech_2_end_to_end_speech_recognition",
        "neural_message_passing_quantum_chemistry",
        "machine_super_intelligence",
    ]
    by_id = {paper["id"]: paper for paper in metadata}
    full = [paper["id"] for paper in metadata]
    lines = [
        "# Keith Reading Plan",
        "",
        "## A. 10-Paper Practical Fast Track",
        "",
        *[f"{i}. **{by_id[paper_id]['title']}** - read for {by_id[paper_id]['category']} implications." for i, paper_id in enumerate(fast, start=1)],
        "",
        "## B. 26-Paper Full Track",
        "",
        *[f"{i}. **{by_id[paper_id]['title']}**" for i, paper_id in enumerate(full, start=1)],
        "",
        "## C. Reading Order",
        "",
        "Start with MDL/evaluation humility, then sequence memory, then attention/retrieval, then scaling, then multimodal, then reasoning/memory. This mirrors the project path from deterministic signals to optional research sidecars.",
        "",
        "## D. What To Skim Vs Read Deeply",
        "",
        "- Read deeply: MDL tutorial, Understanding LSTMs, Pointer Networks, Attention Is All You Need, Scaling Laws, Deep Speech 2.",
        "- Skim for architecture intuition: ResNet papers, dilated convolutions, ImageNet/AlexNet, CS231n.",
        "- Skim for caution and vocabulary: Machine Super Intelligence, Kolmogorov book page, complexodynamics posts.",
        "",
        "## E. What To Implement After Each Cluster",
        "",
        "- MDL/compression: boilerplate and simplicity checks.",
        "- Sequence models: section chronology and callback diagnostics.",
        "- Attention/pointers: evidence-span ranking and retrieval evaluation.",
        "- Scaling: transcript-count gates and learning curves.",
        "- Speech/multimodal: ASR provenance and text+prosody ablations.",
        "- Relation/memory: Q&A pair graph and topic-thread memory.",
        "",
        "## F. How Each Cluster Maps To Signal Engine 2.0",
        "",
        "- Fundamentals: keep sidecars additive and ablated.",
        "- Sequence: model calls as ordered, sectioned conversations.",
        "- Attention: retrieve and cite evidence before generating claims.",
        "- Scaling: increase data before increasing model ambition.",
        "- Multimodal: join audio/video to text only after media quality gates.",
        "- Complexity/MDL: favor simple explanations until complex models prove lift.",
        "",
        "## G. Plain-English Cheat Sheet",
        "",
        "- Do not start by training a big model.",
        "- Start by making the transcript evidence better.",
        "- Every signal needs a quote, section, and failure mode.",
        "- Retrieval is useful only if it helps the reviewer find the right evidence.",
        "- Audio/video are future sidecars, not current proof.",
        "- The portfolio story is discipline: research taste plus honest engineering.",
    ]
    (DOC_DIR / "keith_reading_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deep paper briefs and synthesis assets.")
    parser.add_argument("--metadata", default=str(DATA_DIR / "papers_metadata.json"))
    parser.add_argument("--registry", default=str(DATA_DIR / "source_registry.json"))
    parser.add_argument("--extracted-dir", default=str(DATA_DIR / "extracted"))
    args = parser.parse_args()

    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    registry_by_id = {entry["id"]: entry for entry in registry}
    extracted_dir = Path(args.extracted_dir)
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)

    for paper in metadata:
        extracted_path = extracted_dir / f"{paper['id']}.json"
        extracted = json.loads(extracted_path.read_text(encoding="utf-8")) if extracted_path.exists() else {}
        output = PAPERS_DIR / FILENAME_MAP[paper["id"]]
        output.write_text(_brief(paper, registry_by_id[paper["id"]], extracted), encoding="utf-8")

    _write_feature_backlog(metadata)
    _write_synthesis(metadata, registry_by_id)
    _write_reading_plan(metadata)
    print(f"Built {len(metadata)} paper briefs plus synthesis, backlog, and reading plan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
