# Corpus Evaluation Implementation Report

## What Was Added

- Tiny corpus manifests in CSV and JSON.
- Tiny gold-label JSONL examples covering guidance revision, analyst pressure, management hedging, uncertainty, opportunity commitment, risk friction, and neutral labels.
- Standard-library validators for manifests and gold labels.
- Standard-library signal-output evaluator for JSONL predictions.
- Standard-library error-analysis report generator.
- Documentation for corpus buildout, evaluation rubric, guidance extraction, Q&A friction, false-positive control, provenance, and model/retrieval roadmap.
- Targeted tests and a tiny prediction fixture.

## Scaffold Only

- No transcripts were downloaded.
- No source URLs are proof of downloaded or licensed transcripts.
- No generated heavy artifacts were added.
- No canonical extraction behavior was changed.
- No dependencies were added.
- No production ML system was implemented.

## Blunt Boundaries

- Synthetic support/sales/account data does not prove product value.
- A few earnings-call demos do not prove repeatability.
- No statistical significance exists yet.
- Next credibility unlock is a real manually reviewed 30-call corpus, then 100-150 calls.
- Retrieval and embeddings should wait until deterministic benchmarking and error analysis are working.

## Validation Results

- `python -m py_compile scripts/validate_corpus_manifest.py scripts/validate_gold_labels.py scripts/evaluate_signal_outputs.py scripts/build_error_analysis.py`: passed.
- `python -m pytest tests/test_validate_corpus_manifest.py tests/test_validate_gold_labels.py tests/test_evaluate_signal_outputs.py -q`: passed, 9 tests.
- `python scripts/check_markdown_links.py docs/corpus-build-plan.md docs/evaluation-rubric.md docs/ideal-30-call-download-list.md docs/guidance-extraction-spec.md docs/qa-friction-spec.md docs/false-positive-control.md docs/provenance-and-evidence-spans.md docs/nlp-model-and-retrieval-roadmap.md`: passed.
- `python scripts/validate_corpus_manifest.py --path data/corpus_manifest.example.csv`: passed, 8 rows.
- `python scripts/validate_corpus_manifest.py --path data/corpus_manifest.example.json`: passed, 8 rows.
- `python scripts/validate_gold_labels.py --path data/gold_labels.example.jsonl`: passed, 7 rows.
- `python scripts/evaluate_signal_outputs.py --gold-labels data/gold_labels.example.jsonl --predictions tests/fixtures/tiny_signal_predictions.jsonl --report-out /tmp/signal_engine_eval_report.md --json-out /tmp/signal_engine_eval_summary.json`: passed, 5 matched, 2 unmatched, 1 potential false positive, 1 missing evidence, 1 direction mismatch.
- `python scripts/build_error_analysis.py --evaluation-json /tmp/signal_engine_eval_summary.json --out /tmp/signal_engine_error_analysis.md`: passed.

## Files Changed

- `data/corpus_manifest.example.csv`
- `data/corpus_manifest.example.json`
- `data/gold_labels.example.jsonl`
- `docs/corpus-build-plan.md`
- `docs/ideal-30-call-download-list.md`
- `docs/evaluation-rubric.md`
- `docs/guidance-extraction-spec.md`
- `docs/qa-friction-spec.md`
- `docs/false-positive-control.md`
- `docs/provenance-and-evidence-spans.md`
- `docs/nlp-model-and-retrieval-roadmap.md`
- `docs/corpus-evaluation-implementation-report.md`
- `scripts/validate_corpus_manifest.py`
- `scripts/validate_gold_labels.py`
- `scripts/evaluate_signal_outputs.py`
- `scripts/build_error_analysis.py`
- `tests/test_validate_corpus_manifest.py`
- `tests/test_validate_gold_labels.py`
- `tests/test_evaluate_signal_outputs.py`
- `tests/fixtures/tiny_signal_predictions.jsonl`

## Next 10 Tasks

1. Manually confirm source availability for the first 30 target calls.
2. Create a real working manifest separate from the example manifest.
3. Download only permitted transcript text.
4. Parse transcripts into prepared remarks and Q&A sections.
5. Add reviewer-owned weak/manual labels.
6. Run the validators on every manifest and label update.
7. Generate deterministic predictions into JSONL.
8. Run error analysis after each rule pass.
9. Promote only cases with clear provenance and evidence spans.
10. Expand toward 100-150 calls only after the first 30 are stable.

## Keith's Manual-Download Checklist

- Confirm source rights and access manually.
- Record source URL and source category.
- Save only permitted transcript text.
- Record local transcript path.
- Mark transcript status accurately.
- Add manual notes for licensing, quality, or sectioning issues.
- Label with short evidence text and reviewer name in the real label file.
- Keep blocked cases in the manifest instead of deleting them.
