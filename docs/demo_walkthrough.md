# Demo Walkthrough

## 3-minute script

### 1. Problem

Generic AI summaries can sound useful while hiding the evidence. For business communication, the hard part is not just summarizing a call; it is showing what was detected, where it came from, how it was reviewed, and whether the workflow is improving.

### 2. What the repo does

Signal Engine 2.0 turns transcripts into evidence-backed signal candidates, preserves source/provenance, creates human-review packets, and evaluates deterministic outputs against reviewed labels. ML and retrieval exist as benchmark/support layers, not as replacements for the transcript-first path.

### 3. Show the workflow

Start with intake and source discovery. The system records candidate public sources, rejects blocked/paywalled paths, and keeps provenance separate from labels.

Then show deterministic extraction. The output is a set of candidate spans that can be reviewed, corrected, or rejected. Weak labels are suggestions only.

Then show the review packet. A reviewer can inspect evidence and decide what should enter the gold-label set.

### 4. Show evaluation/reporting

Open:

- `reports/evaluation_readiness.json`
- `reports/source_quality_metric_comparison.md`
- `reports/experiment_results/local_ml_baseline.md`
- `reports/retrieval_eval.md`
- `reports/demo/portfolio_demo_report.md`

The useful story is measurable progress: deterministic metrics, source-quality subsets, a benchmark-only TF-IDF/logistic-regression baseline, and a retrieval gate that stays closed until enough labels exist.

### 5. Current limits

The benchmark is small and mixed-provenance. The repo does not claim production readiness, trading alpha, statistical significance, or automated investment advice.

### 6. Next scaling step

Complete the 100-call corpus and grow the reviewed label set toward 500-1,000 accepted labels. That would make source-quality slices, model comparisons, and retrieval evaluation more meaningful.
