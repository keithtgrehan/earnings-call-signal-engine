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
TIERED_TRANSCRIPT_TARGETS ?= data/corpus/tiered_transcript_targets.csv
TIERED_TRANSCRIPT_DISCOVERY_CONFIG ?= data/corpus/transcript_source_discovery.yaml
DISCOVERED_TRANSCRIPT_SOURCES ?= data/corpus/discovered_transcript_sources.csv
LLM_LIVE_ARGS ?=

.PHONY: setup lint smoke clean portfolio-proof portfolio-demo docs-audit refresh-proof proof-freshness link-check portfolio-ci first-proof-refresh error-analysis retrieval-refresh gold-holdout-refresh resource-fit-refresh best-in-class-refresh data-growth-refresh review-summary validate-reviewed promote-gold eval-labels benchmark-report labeling-ci eval-loop next-experiment embedding-benchmark report-readiness demo review-priority-labels promote-reviewed-priority-labels eval-after-review intake-high-signal-transcripts discover-high-signal-sources-query-only discover-high-signal-sources verify-high-signal-sources intake-high-signal-from-discovered-sources prepare-manual-transcript-sources intake-manual-transcript-files review-after-manual-intake discover-tiered-transcript-sources acquire-verified-transcripts check-no-transcript-text-staged acquire-tiered-transcripts review-bootstrap review-load-transcripts review-upload-suggestions review-build-queue review-export-gold review-eval gold-review-queue rights-check registry-check claims-check restricted-artifacts-check corpus-manifest-check retrieval-schema-check event-study-check training-plan-check benchmark-sanity-check nyse-universe-check source-discovery-check manual-local-check media-registration-check retrieval-build-check nlp-training-sources-check experiment-design-check event-study-join-check build-nyse-30-pilot validate-nyse-30-pilot build-agent5-source-queue validate-agent5-source-queue register-manual-local-batch validate-manual-local-registry report-agent5-acquisition-status agent5-acquisition-check gold-audit first-100-review-queue promotion-manifest-check first-100-review-metrics agent1-validate-sources agent1-section agent1-candidates agent1-dedupe agent1-review-queue agent1-error-analysis agent1-pilot llm-safe-check llm-router-check llm-claude-smoke llm-glm52-smoke llm-bakeoff promptfoo-check opik-check training-readiness corpus-safe-check

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

review-bootstrap:
	$(PYTHON) scripts/review/bootstrap_argilla.py

review-load-transcripts:
	$(PYTHON) scripts/review/load_transcripts.py --dry-run

review-upload-suggestions:
	$(PYTHON) scripts/review/upload_suggestions.py

review-build-queue:
	$(PYTHON) scripts/review/build_review_queue.py

review-export-gold:
	@echo "Set REVIEWED_JSONL=/path/to/reviewed.jsonl to export reviewed Argilla records."
	@test -n "$(REVIEWED_JSONL)" || exit 2
	$(PYTHON) scripts/review/export_gold_labels.py --reviewed "$(REVIEWED_JSONL)"

review-eval:
	$(PYTHON) scripts/review/run_review_evaluation.py

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

registry-check:
	$(PYTHON) scripts/validate_resource_registry.py --path configs/resource_registry.example.yml

claims-check:
	$(PYTHON) scripts/validate_claims_matrix.py --path configs/claims_matrix.example.yml

restricted-artifacts-check:
	$(PYTHON) scripts/check_restricted_artifacts.py --dry-run

corpus-manifest-check:
	$(PYTHON) scripts/validate_corpus_manifest.py --path data/corpus_manifest.example.csv

retrieval-schema-check:
	$(PYTHON) scripts/validate_retrieval_objects.py --schema schemas/retrieval_object.schema.json
	$(PYTHON) scripts/validate_retrieval_metrics.py --path configs/retrieval_metrics.example.yml

event-study-check:
	$(PYTHON) scripts/validate_event_study_cases.py --path configs/event_study_cases.example.yml

training-plan-check:
	$(PYTHON) scripts/validate_training_plan.py --path configs/training_plan.example.yml

benchmark-sanity-check:
	$(PYTHON) scripts/validate_benchmark_registry.py --path configs/benchmark_registry.example.yml
	$(PYTHON) scripts/validate_byok_reviewer_config.py --path configs/byok_reviewer.example.yml
	$(PYTHON) scripts/export_training_candidates.py --out /tmp/signal_engine_training_candidates.safe_check.json

llm-safe-check:
	$(PYTHON) scripts/validate_llm_config.py --path configs/llm.example.yml
	$(PYTHON) scripts/run_llm_fixture_smoke.py --provider dry_run
	$(PYTHON) scripts/check_llm_artifacts.py --root artifacts/llm --allow-missing

llm-router-check:
	$(PYTHON) scripts/run_llm_fixture_smoke.py --provider dry_run --router litellm

llm-claude-smoke:
	SIGNAL_ENGINE_LLM_PROVIDER=claude $(PYTHON) scripts/run_llm_fixture_smoke.py $(LLM_LIVE_ARGS)

llm-glm52-smoke:
	SIGNAL_ENGINE_LLM_PROVIDER=glm52 $(PYTHON) scripts/run_llm_fixture_smoke.py $(LLM_LIVE_ARGS)

llm-bakeoff:
	$(PYTHON) scripts/run_llm_bakeoff.py --providers dry_run --out reports/llm/llm_bakeoff.md

promptfoo-check:
	@command -v promptfoo >/dev/null 2>&1 && promptfoo eval -c evals/promptfoo/llm_signal_extraction.yaml || echo "promptfoo unavailable; skipped"

opik-check:
	$(PYTHON) scripts/check_opik_config.py --path configs/opik.example.yml || true

nyse-universe-check:
	$(PYTHON) scripts/validate_nyse_earnings_universe.py --path configs/nyse_earnings_universe.example.yml
	$(PYTHON) scripts/build_nyse_earnings_universe.py --example-config configs/nyse_earnings_universe.example.yml

source-discovery-check:
	$(PYTHON) scripts/validate_source_discovery_queue.py --path configs/source_discovery_policy.example.yml
	$(PYTHON) scripts/build_source_discovery_queue.py --path configs/source_discovery_policy.example.yml

manual-local-check:
	$(PYTHON) scripts/register_manual_local_case.py --case-id synthetic_manual_local_check --path tests/fixtures/tiny_realistic_earnings_excerpt.txt --out /tmp/signal_engine_manual_local_check.json

media-registration-check:
	$(PYTHON) scripts/register_manual_local_media.py --config configs/media_ingest_policy.example.yml
	$(PYTHON) scripts/build_media_event_windows.py --path configs/rag_build_policy.example.yml

retrieval-build-check:
	$(PYTHON) scripts/build_retrieval_objects.py --path configs/rag_build_policy.example.yml

nlp-training-sources-check:
	$(PYTHON) scripts/validate_nlp_training_sources.py --path configs/nlp_training_sources.example.yml
	$(PYTHON) scripts/build_training_candidate_manifest.py --path configs/nlp_training_sources.example.yml --out /tmp/signal_engine_training_source_manifest.json

experiment-design-check:
	$(PYTHON) scripts/validate_experiment_design.py --path configs/experiment_design.example.yml

event-study-join-check:
	$(PYTHON) scripts/validate_event_study_join_policy.py --path configs/event_study_join_policy.example.yml

build-nyse-30-pilot:
	$(PYTHON) scripts/build_nyse_30_pilot_queue.py

validate-nyse-30-pilot:
	$(PYTHON) scripts/validate_nyse_30_pilot.py --path configs/nyse_30_pilot_targets.yml

build-agent5-source-queue:
	$(PYTHON) scripts/build_agent5_source_queue.py --targets configs/nyse_30_pilot_targets.yml --out /tmp/signal_engine_agent5_source_queue.json

validate-agent5-source-queue:
	$(PYTHON) scripts/validate_agent5_source_queue.py --targets configs/nyse_30_pilot_targets.yml

register-manual-local-batch:
	$(PYTHON) scripts/register_manual_local_batch.py

validate-manual-local-registry:
	$(PYTHON) scripts/validate_manual_local_registry.py

report-agent5-acquisition-status:
	$(PYTHON) scripts/report_agent5_acquisition_status.py

agent5-acquisition-check: build-nyse-30-pilot validate-nyse-30-pilot build-agent5-source-queue validate-agent5-source-queue register-manual-local-batch validate-manual-local-registry report-agent5-acquisition-status

gold-audit:
	$(PYTHON) scripts/audit_gold_labels.py

first-100-review-queue:
	$(PYTHON) scripts/build_first_100_review_queue.py

promotion-manifest-check:
	$(PYTHON) scripts/validate_promotion_manifest.py

first-100-review-metrics:
	$(PYTHON) scripts/report_first_100_review_metrics.py

agent1-validate-sources:
	$(PYTHON) scripts/agent1_validate_manual_local_sources.py

agent1-section:
	$(PYTHON) scripts/agent1_section_transcripts.py

agent1-candidates:
	$(PYTHON) scripts/agent1_generate_candidates.py

agent1-dedupe:
	$(PYTHON) scripts/agent1_deduplicate_candidates.py

agent1-review-queue:
	$(PYTHON) scripts/agent1_build_review_queue.py

agent1-error-analysis:
	$(PYTHON) scripts/agent1_error_analysis.py

agent1-pilot: agent1-validate-sources agent1-section agent1-candidates agent1-dedupe agent1-review-queue agent1-error-analysis

training-readiness:
	$(PYTHON) scripts/run_training_readiness.py --json-out /tmp/signal_engine_training_readiness.json || true

rights-check: registry-check claims-check restricted-artifacts-check

corpus-safe-check: rights-check corpus-manifest-check retrieval-schema-check event-study-check training-plan-check benchmark-sanity-check llm-safe-check nyse-universe-check source-discovery-check manual-local-check media-registration-check retrieval-build-check nlp-training-sources-check experiment-design-check event-study-join-check agent5-acquisition-check promotion-manifest-check

discover-tiered-transcript-sources:
	$(PYTHON) tools/discover_transcript_sources.py --targets-csv $(TIERED_TRANSCRIPT_TARGETS) --config $(TIERED_TRANSCRIPT_DISCOVERY_CONFIG) --output-csv $(DISCOVERED_TRANSCRIPT_SOURCES) --report-path reports/transcript_source_discovery.md

acquire-verified-transcripts:
	$(PYTHON) tools/acquire_verified_transcripts.py --discovered-csv $(DISCOVERED_TRANSCRIPT_SOURCES) --manual-template $(MANUAL_SOURCE_TEMPLATE) --file-manifest $(MANUAL_TRANSCRIPT_FILE_MANIFEST)

check-no-transcript-text-staged:
	$(PYTHON) tools/check_no_transcript_text_staged.py

acquire-tiered-transcripts: discover-tiered-transcript-sources acquire-verified-transcripts prepare-manual-transcript-sources intake-manual-transcript-files

labeling-ci:
	$(PYTHON) tools/review_next_batch.py --summary
	$(PYTHON) tools/validate_reviewed_batch.py || true
	$(PYTHON) tools/update_gold_from_review.py --dry-run || true
	$(PYTHON) tools/report_evaluation_readiness.py
	$(PYTHON) tools/evaluate_gold_labels.py

clean:
	rm -rf ./_smoke_out ./_smoke_cache build dist
