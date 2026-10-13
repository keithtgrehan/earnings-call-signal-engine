# Signal Engine

**Find the passages worth reviewing in an earnings call—and keep the evidence attached.**

[View the offline demo report](reports/demo/portfolio_demo_report.md) · [Follow the walkthrough](docs/demo_walkthrough.md) · [Review the architecture](docs/portfolio_architecture.md)

Signal Engine is a portfolio prototype for structured company research. It turns earnings-call transcripts into reviewable signal candidates, supporting evidence and evaluation reports. The core uses deterministic rules to identify guidance language, uncertainty, risk and analyst-management friction; a reviewer can inspect the original passage before accepting an interpretation.

The product question is simple: **how can a useful summary also be something another person can check?**

## Start here: a three-minute review

1. Read the [demo report](reports/demo/portfolio_demo_report.md) for the end-to-end workflow and the scope of the recorded benchmark.
2. Open the [human-review workflow](docs/review_workflow.md) to see how candidates are reviewed, corrected and accepted.
3. Read the [evaluation strategy](docs/evaluation_strategy.md) to see why source quality and reviewed examples matter more than a headline score.
4. Use the [technical reviewer brief](docs/technical_reviewer_brief.md) for a deeper implementation review.

These materials can be inspected directly on GitHub. The offline report can also be rebuilt locally without downloading transcripts or calling a model.

## What works

| Capability | Reviewer value |
| --- | --- |
| Transcript intake with source and provenance records | Trace an analysis back to the material it used. |
| Deterministic signal extraction | Inspect repeatable candidates and supporting text rather than an unexplained conclusion. |
| Human-review packets and a local Argilla workflow | Accept, reject or correct candidates before treating them as reviewed labels. |
| Evaluation against labelled examples | Inspect precision, recall, F1 and differences between source-quality subsets. |
| A TF-IDF/logistic-regression comparison | Compare a conventional ML baseline with the rule-based approach before adding model complexity. |
| Offline portfolio reporting | Review committed evidence without live acquisition or paid API access. |

## Why these design choices

**Evidence before interpretation.** A confident summary is difficult to challenge if its sources disappear. Signal candidates retain transcript evidence so the reviewer can assess context and distinguish wording from inference.

**Human review before accepted labels.** Machine suggestions can organise a review queue, but they cannot certify their own correctness. Accepted labels require a separate review step. This keeps extraction, review and evaluation from becoming a circular process.

**A measurable baseline before more AI.** Deterministic extraction is the reference path. The classical ML baseline is a comparison, not an automatic replacement. Retrieval and model-assisted review are developed behind explicit readiness gates so added complexity has to earn its place.

**Reproducible review before broad acquisition.** The portfolio route uses committed reports and controlled local workflows. Source registration and acquisition are separate, preserving provenance and source-use restrictions rather than assuming that every readable transcript can be redistributed.

**A narrow output before a broad promise.** This project helps inspect language in business communication. It does not turn a risk phrase into a prediction of business performance or a trading recommendation.

## Commercial relevance

A sales or partnerships professional often has to turn a large amount of company information into a small number of useful questions. This project explores the analytical work behind that task: identify a relevant passage, preserve its context, test an interpretation and explain what would need further validation.

The same review pattern is relevant to discovery, customer feedback and account research. Those are transferable applications of the design, rather than claims that all of those products are implemented here.

This is Keith Grehan's portfolio work, developed with AI-assisted tooling. It demonstrates product scoping, technical learning and evaluation judgement alongside a commercial background.

## Architecture

```text
Transcript + provenance → rule-based candidates → human review
                                                   ↓
                                      accepted labels → evaluation
```

Python provides the core tooling. Review packets, schemas and command-line workflows keep individual stages inspectable. Optional review and ML dependencies sit alongside the deterministic core.

| Layer | Status in this portfolio |
| --- | --- |
| Intake, extraction, review workflow and offline reports | Implemented; see the linked workflow and demo evidence. |
| Classical ML evaluation | Benchmark comparison on a small dataset. |
| Retrieval, model review and multimodal extensions | Supporting infrastructure and experiments with separate readiness gates; not required for the core demo. |
| Custom training at scale and broad performance claims | Reserved for sufficient rights-cleared, human-reviewed evidence. |

## Run the offline report

Python 3.11 or newer is required. From the repository root:

```bash
make portfolio-demo
```

This rebuilds the portfolio report, metrics JSON and walkthrough under `reports/demo/` from **existing committed reports**. It does not run a new extraction benchmark, fetch transcripts or promote labels. The report builder uses the Python standard library.

For the wider toolkit:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

The [manual-source workflow](docs/manual_transcript_source_workflow.md) describes transcript intake. The [Argilla setup](docs/argilla_setup.md) documents the optional local review environment.

## Evidence and technical review

- [Evaluation strategy](docs/evaluation_strategy.md) — methods, subset comparisons and interpretation.
- [Source-quality comparison](reports/source_quality_metric_comparison.md) — the evidence behind dataset-quality decisions.
- [Architecture](docs/portfolio_architecture.md) — stage boundaries and reusable design.
- [Review workflow](docs/review_workflow.md) — how candidate labels become accepted evidence.
- [Data and corpus policy](docs/data_rights_and_corpus_policy.md) — source handling and provenance.
- [Tests](tests/) — implementation checks for the repository's components.

The committed benchmark is small and mixed in provenance. It supports inspection of the workflow, not a claim of production accuracy, statistical significance or trading returns. Detailed results remain linked so reviewers can assess the evidence themselves.

Documentation links can be checked with:

```bash
python3 scripts/check_markdown_links.py README.md
```
