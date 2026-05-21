PYTHON := python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
CLI := $(VENV)/bin/earnings-call-sentiment

SMOKE_URL ?= https://www.youtube.com/watch?v=BaW_jenozKc
SMOKE_OUT := ./_smoke_out
SMOKE_CACHE := ./_smoke_cache
HIGH_SIGNAL_SEARCH_RESULTS_FILE ?= data/corpus/high_signal_search_results.csv
HIGH_SIGNAL_CANDIDATE_URL_FILE ?= data/corpus/high_signal_candidate_urls.csv
HIGH_SIGNAL_SOURCE_URL_FILE ?= data/corpus/high_signal_source_urls.csv
MANUAL_SOURCE_TEMPLATE ?= data/corpus/manual_source_template.csv
MANUAL_TRANSCRIPT_FILE_MANIFEST ?= data/corpus/manual_transcript_file_manifest.csv

.PHONY: setup lint smoke clean portfolio-proof portfolio-demo docs-audit refresh-proof proof-freshness link-check portfolio-ci first-proof-refresh error-analysis retrieval-refresh gold-holdout-refresh resource-fit-refresh best-in-class-refresh data-growth-refresh review-summary validate-reviewed promote-gold eval-labels benchmark-report labeling-ci eval-loop next-experiment embedding-benchmark report-readiness demo review-priority-labels promote-reviewed-priority-labels eval-after-review intake-high-signal-transcripts discover-high-signal-sources-query-only discover-high-signal-sources verify-high-signal-sources intake-high-signal-from-discovered-sources prepare-manual-transcript-sources intake-manual-transcript-files review-after-manual-intake gold-review-queue

$(VENV_PY):
	$(PYTHON) -m venv $(VENV)

setup: $(VENV_PY)
	$(VENV_PIP) install -U pip
	$(VENV_PIP) install -r requirements.txt
	$(VENV_PIP) install -e .

lint: setup
	$(VENV_PIP) install ruff
	$(RUFF) check src
	$(VENV_PY) -m py_compile $$(find src -type f -name "*.py")

smoke: setup
	mkdir -p $(SMOKE_OUT) $(SMOKE_CACHE)
	$(CLI) \
		--youtube-url '$(SMOKE_URL)' \
		--cache-dir $(SMOKE_CACHE) \
		--out-dir $(SMOKE_OUT)
	@echo
	@echo "Smoke artifacts:"
	@ls -la $(SMOKE_OUT) $(SMOKE_CACHE)

portfolio-proof:
	$(PYTHON) scripts/build_portfolio_proof.py

portfolio-demo:
	$(PYTHON) tools/build_portfolio_demo.py

docs-audit:
	$(PYTHON) scripts/audit_portfolio_docs.py

refresh-proof:
	$(PYTHON) scripts/refresh_readme_proof.py

proof-freshness:
	$(PYTHON) scripts/check_proof_freshness.py

link-check:
	$(PYTHON) scripts/check_markdown_links.py

portfolio-ci:
	@set -e; \
	VERIFY_LOG=.portfolio_ci_verify.log; \
	echo "== build canonical proof =="; \
	if $(PYTHON) scripts/verify_outputs.py --out-dir outputs/LLY_2025_Q2_call08 --require-run-meta > $$VERIFY_LOG 2>&1; then \
		$(PYTHON) scripts/build_portfolio_proof.py; \
		echo "== refresh README proof block =="; \
		$(PYTHON) scripts/refresh_readme_proof.py; \
		echo "== check proof freshness =="; \
		$(PYTHON) scripts/check_proof_freshness.py; \
		echo "== audit canonical portfolio docs =="; \
		$(PYTHON) scripts/audit_portfolio_docs.py; \
		echo "== verify canonical outputs =="; \
		cat $$VERIFY_LOG; \
	else \
		echo "Portfolio CI warning: local legacy proof artifacts for outputs/LLY_2025_Q2_call08 are incomplete; skipping legacy proof refresh/freshness/doc-audit steps."; \
		cat $$VERIFY_LOG; \
		$(PYTHON) scripts/build_portfolio_proof.py; \
	fi; \
	echo "== check markdown links =="; \
	$(PYTHON) scripts/check_markdown_links.py; \
	echo "== compile portfolio scripts =="; \
	$(PYTHON) -m py_compile app/site_server.py scripts/build_portfolio_proof.py scripts/audit_portfolio_docs.py scripts/refresh_readme_proof.py scripts/check_markdown_links.py scripts/check_proof_freshness.py; \
	rm -f $$VERIFY_LOG; \
	echo "PORTFOLIO CI PASS: link integrity and syntax checks completed, with legacy proof steps run when the canonical LLY bundle is present or skipped with a warning when it is incomplete."

first-proof-refresh:
	$(PYTHON) scripts/build_human_reviewed_signal_labels.py
	$(PYTHON) scripts/build_label_review_packet.py
	$(PYTHON) scripts/evaluate_signal_baseline.py
	$(PYTHON) scripts/evaluate_label_agreement.py
	$(PYTHON) scripts/build_multimodal_pilot_cases.py
	$(PYTHON) scripts/build_audio_pilot_intake.py
	$(PYTHON) scripts/validate_audio_pilot_assets.py
	$(PYTHON) scripts/evaluate_multimodal_pilot.py
	$(PYTHON) scripts/evaluate_multimodal_lift.py

resource-fit-refresh:
	$(PYTHON) scripts/build_public_resource_fit_manifest.py

error-analysis:
	$(PYTHON) scripts/analyze_signal_errors.py

gold-holdout-refresh:
	$(PYTHON) scripts/build_gold_holdout_set.py

retrieval-refresh:
	$(PYTHON) scripts/build_signal_retrieval_index.py

best-in-class-refresh: first-proof-refresh
	$(PYTHON) scripts/build_public_resource_fit_manifest.py
	$(PYTHON) scripts/evaluate_signal_baseline.py
	$(PYTHON) scripts/analyze_signal_errors.py
	$(PYTHON) scripts/build_gold_holdout_set.py
	$(PYTHON) scripts/build_signal_retrieval_index.py
	$(PYTHON) scripts/prioritize_second_review.py
	$(PYTHON) scripts/evaluate_label_agreement.py
	$(PYTHON) scripts/evaluate_multimodal_pilot.py

data-growth-refresh:
	$(PYTHON) scripts/import_loughran_mcdonald.py
	$(PYTHON) scripts/import_financial_phrasebank.py
	$(PYTHON) scripts/mine_signal_label_candidates.py
	$(PYTHON) scripts/promote_reviewed_label_candidates.py
	$(PYTHON) scripts/report_label_dataset_growth.py
	$(PYTHON) scripts/evaluate_signal_baseline.py
	$(PYTHON) scripts/analyze_signal_errors.py || true
	$(PYTHON) scripts/build_label_review_packet.py
	$(PYTHON) scripts/prioritize_second_review.py || true

review-summary:
	$(PYTHON) tools/review_next_batch.py --summary

validate-reviewed:
	$(PYTHON) tools/validate_reviewed_batch.py

promote-gold:
	$(PYTHON) tools/update_gold_from_review.py

eval-labels:
	$(PYTHON) tools/report_evaluation_readiness.py
	$(PYTHON) tools/evaluate_gold_labels.py

benchmark-report:
	$(PYTHON) tools/report_evaluation_readiness.py

eval-loop:
	$(PYTHON) tools/run_evaluation_loop.py

next-experiment:
	$(PYTHON) tools/run_next_experiment.py

embedding-benchmark:
	$(PYTHON) tools/run_embedding_benchmark.py

report-readiness:
	$(PYTHON) tools/report_evaluation_readiness.py
	$(PYTHON) tools/run_evaluation_loop.py

demo:
	$(PYTHON) tools/run_evaluation_loop.py
	$(PYTHON) tools/run_next_experiment.py || true
	$(PYTHON) tools/build_evidence_objects.py
	$(PYTHON) tools/run_retrieval_benchmark.py || true
	$(PYTHON) tools/build_demo_artifacts.py

review-priority-labels:
	$(PYTHON) tools/prepare_priority_review.py

promote-reviewed-priority-labels:
	$(PYTHON) tools/promote_priority_review.py

eval-after-review:
	$(PYTHON) tools/promote_priority_review.py
	$(PYTHON) tools/run_evaluation_loop.py
	$(PYTHON) tools/filter_gold_labels.py --write-reports
	$(PYTHON) tools/run_next_experiment.py || true
	$(PYTHON) tools/run_retrieval_benchmark.py || true
	$(PYTHON) tools/report_priority_review_validation.py

intake-high-signal-transcripts:
	$(PYTHON) tools/intake_high_signal_transcripts.py --tickers NVDA MSFT GOOGL AMZN META AAPL AMD ASML TSM AVGO CRM SNOW HUBS NOW DDOG NET MDB PANW CRWD TSLA SHOP UBER RBLX COIN PLTR --latest-calls 4 --output-root data/corpus/high_signal_cases --min-transcript-chars 5000 --require-markers --rate-limit-seconds 3

discover-high-signal-sources-query-only:
	$(PYTHON) tools/discover_high_signal_transcript_sources.py --query-only

discover-high-signal-sources:
	$(PYTHON) tools/discover_high_signal_transcript_sources.py --search-results-file $(HIGH_SIGNAL_SEARCH_RESULTS_FILE)

verify-high-signal-sources:
	$(PYTHON) tools/discover_high_signal_transcript_sources.py --verify-only --source-url-file $(HIGH_SIGNAL_CANDIDATE_URL_FILE)

intake-high-signal-from-discovered-sources:
	$(PYTHON) tools/intake_high_signal_transcripts.py --source-url-file $(HIGH_SIGNAL_SOURCE_URL_FILE) --tickers NVDA MSFT GOOGL AMZN META AAPL AMD ASML TSM AVGO CRM SNOW HUBS NOW DDOG NET MDB PANW CRWD TSLA SHOP UBER RBLX COIN PLTR --latest-calls 4 --output-root data/corpus/high_signal_cases --min-transcript-chars 5000 --require-markers --rate-limit-seconds 3

prepare-manual-transcript-sources:
	$(PYTHON) tools/prepare_manual_transcript_sources.py --input-csv $(MANUAL_SOURCE_TEMPLATE) --output-csv $(HIGH_SIGNAL_SOURCE_URL_FILE) --file-manifest $(MANUAL_TRANSCRIPT_FILE_MANIFEST) --report-path reports/manual_source_validation.md --min-transcript-chars 5000 --require-markers

intake-manual-transcript-files:
	$(PYTHON) tools/intake_high_signal_transcripts.py --source manual_file_manifest --manual-file-manifest $(MANUAL_TRANSCRIPT_FILE_MANIFEST) --output-root data/corpus/high_signal_cases --min-transcript-chars 5000 --require-markers --rate-limit-seconds 0

review-after-manual-intake:
	$(PYTHON) tools/prepare_priority_review.py
	$(PYTHON) tools/report_priority_review_validation.py

gold-review-queue:
	PYTHONPATH=src $(PYTHON) -m signal_engine.review_queue.build \
		--packets 'data/corpus/high_signal_cases/*/labels/human_labeling_packet.md' \
		--transcripts data/corpus/high_signal_cases \
		--out artifacts/gold_review

labeling-ci:
	$(PYTHON) tools/review_next_batch.py --summary
	$(PYTHON) tools/validate_reviewed_batch.py || true
	$(PYTHON) tools/update_gold_from_review.py --dry-run || true
	$(PYTHON) tools/report_evaluation_readiness.py
	$(PYTHON) tools/evaluate_gold_labels.py

clean:
	rm -rf ./_smoke_out ./_smoke_cache build dist
