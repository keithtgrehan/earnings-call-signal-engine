# Signal Engine

Signal Engine is a deterministic-first signal extraction and evaluation system for long-form business communication.

The current proof path is earnings-call transcripts because public-company sources, explicit guidance language, analyst Q&A, and evidence-span review create a credible route to repeatable evaluation. This repo does not claim production ML, statistical significance, market-reaction proof, alpha, trading edge, stock prediction, or investment advice.

## Signal Engine 2.0

Signal Engine 2.0 is a transcript-first, deterministic signal extraction system that turns earnings-call transcripts into structured, evidence-backed signals using explainable NLP, exact transcript spans, human-reviewed labels, and conservative evaluation.

The system is designed around this path:

```text
transcript -> deterministic signals -> human review -> gold labels -> evaluation
```

Raw transcripts remain canonical. Derived outputs are audit artifacts, weak-label suggestions, review packets, gold-label files created only from explicit human selections, and conservative evaluation reports.

## Current System (Important)

The current implementation is earnings-call focused.

- One-command case pipeline: `tools/run_case_pipeline.py`
- Pipeline flow: validate -> weak labels -> human packet -> gold conversion if a selected-candidates CSV exists -> evaluation if valid gold labels exist.
- `31/31` active cases processed successfully.
- `0` invalid, failed, or quarantined cases in the latest corpus analysis run.
- Raw transcript mutation check passed.
- Test suite passed at approximately `283` tests.
- `5` gold-label scaffold files exist.
- Current valid gold-label rows: `0`.
- Evaluation is intentionally skipped until human-reviewed labels are added.
- Weak labels are suggestions only and are never automatically promoted to gold labels.

Gold-label evaluation is scaffolded but currently inactive until human-reviewed labels are added. This is intentional.

## Human-in-the-loop Workflow

Run the one-command pipeline for a case:

```bash
python tools/run_case_pipeline.py --case AAPL_2026_Q1
```

Then review the generated packet:

```text
/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/AAPL_2026_Q1/labels/human_labeling_packet.md
```

Fill a selected-candidates CSV using:

```text
docs/selected_gold_candidates_template.csv
```

Convert only the approved candidate IDs into gold labels:

```bash
python tools/run_case_pipeline.py --case AAPL_2026_Q1 --stage gold --selected-csv /path/to/selected_gold_candidates.csv
```

After valid non-empty gold labels exist, rerun the case pipeline or corpus analysis to produce weak-vs-gold evaluation rows. The evaluation layer skips cleanly when valid gold labels are absent.

## What is Proven

- The deterministic earnings-call pipeline executes end to end.
- `31` active earnings-call cases have been processed.
- Raw transcript mutation is avoided and checked.
- Weak-label packet workflow exists.
- Selected-candidate approval workflow exists.
- Evaluation safely skips when no valid gold labels exist.
- The test suite passed at approximately `283` tests.
- Weak labels and gold labels remain separate by design.

## What is Not Proven

- No valid gold-label benchmark exists yet.
- No precision, recall, or F1 claim is made.
- No statistical significance claim is made.
- No alpha, trading edge, stock prediction, or investment-advice claim is made.
- No production ML performance claim is made.
- Sales, support, customer-success, and renewal generalization has not been validated.

## Expanded Scope / Roadmap

The same future architecture can be extended beyond earnings calls:

```text
transcript -> deterministic signals -> human review -> gold labels -> evaluation
```

Roadmap domains:

- Sales: buyer intent, objections, deal risk.
- Customer Success: satisfaction, usage risk, expansion signal.
- Support: issue severity, escalation risk, recurring issue.
- Renewals: churn risk, blockers, value perception.

These domains are roadmap scope only. They are not validated production workflows in the current repo state.

## Validation Commands

Markdown and documentation validation:

```bash
python scripts/check_markdown_links.py
```

Python compile check:

```bash
python3 -m py_compile tools/*.py tools/transcript_downloader/*.py scripts/*.py
```

Test suite:

```bash
pytest -q
```

Gold-label scaffold validation:

```bash
python tools/transcript_downloader/validate_gold_labels.py --root "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
```

Corpus analysis:

```bash
python tools/transcript_downloader/run_corpus_analysis.py --root "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
```

## Key Docs

- [Label taxonomy](docs/label-taxonomy.md)
- [Proof of intelligence](docs/proof-of-intelligence.md)
- [Corpus validation report](docs/corpus-validation-report.md)
- [Gold-label JSONL template](docs/gold-label-jsonl-template.md)
- [Gold-labeling review packet](docs/gold-labeling-review-packet.md)
- [Selected-candidates example](docs/selected_gold_candidates_example.md)
- [Transcript sectioning and labeling playbook](docs/transcript-sectioning-and-labeling-playbook.md)

## Branch Presentation Note

GitHub currently reports `main` as the default branch. The current Signal Engine 2.0 transcript corpus pipeline work lives on `codex/transcript-corpus-pipeline`.
