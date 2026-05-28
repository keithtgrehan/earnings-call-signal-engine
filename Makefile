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

.PHONY: setup lint smoke clean portfolio-proof portfolio-demo docs-audit refresh-proof proof-freshness link-check portfolio-ci first-proof-refresh error-analysis retrieval-refresh gold-holdout-refresh resource-fit-refresh best-in-class-refresh data-growth-refresh review-summary validate-reviewed promote-gold eval-labels benchmark-report labeling-ci eval-loop next-experiment embedding-benchmark report-readiness demo review-priority-labels promote-reviewed-priority-labels eval-after-review intake-high-signal-transcripts discover-high-signal-sources-query-only discover-high-signal-sources verify-high-signal-sources intake-high-signal-from-discovered-sources prepare-manual-transcript-sources intake-manual-transcript-files review-after-manual-intake discover-tiered-transcript-sources acquire-verified-transcripts check-no-transcript-text-staged acquire-tiered-transcripts review-bootstrap review-load-transcripts review-upload-suggestions review-build-queue review-export-gold review-eval gold-review-queue rights-check registry-check claims-check restricted-artifacts-check corpus-manifest-check retrieval-schema-check event-study-check training-plan-check benchmark-sanity-check nyse-universe-check source-discovery-check manual-local-check media-registration-check retrieval-build-check nlp-training-sources-check experiment-design-check event-study-join-check build-nyse-30-pilot validate-nyse-30-pilot build-agent5-source-queue validate-agent5-source-queue register-manual-local-batch validate-manual-local-registry report-agent5-acquisition-status agent5-acquisition-check build-ir-sec-universe build-official-ir-candidate-map build-sec-metadata-queue build-ir-sec-availability-matrix build-ir-sec-permitted-ingest-queue report-manual-local-vs-ir-sec-gap validate-ir-sec-acquisition-policy validate-ir-sec-source-candidates validate-ir-sec-availability-matrix validate-ir-sec-permitted-ingest ir-sec-acquisition-check gold-audit first-100-review-queue promotion-manifest-check first-100-review-metrics agent1-validate-sources agent1-section agent1-candidates agent1-dedupe agent1-review-queue agent1-error-analysis agent1-pilot corpus-safe-check acquisition-validate acquisition-prioritize acquisition-dry-run

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

nyse-universe-check:
	$(PYTHON) scripts/validate_nyse_earnings_universe.py --path configs/nyse_earnings_universe.example.yml
	$(PYTHON) scripts/build_nyse_earnings_universe.py --example-config configs/nyse_earnings_universe.example.yml

source-discovery-check:
	$(PYTHON) scripts/validate_source_discovery_queue.py --path configs/source_discovery_policy.example.yml
	$(PYTHON) scripts/build_source_discovery_queue.py --path configs/source_discovery_policy.example.yml

acquisition-validate:
	$(PYTHON) scripts/validate_source_rights_review_queue.py
	$(PYTHON) scripts/validate_nyse_100_source_approvals.py --input data/acquisition/nyse_100_source_rights_review_queue.csv
	$(PYTHON) scripts/validate_nyse_100_chunk_manifest.py

acquisition-prioritize:
	$(PYTHON) tools/prioritize_source_rights_queue.py

acquisition-dry-run:
	$(PYTHON) tools/acquire_nyse_100_assets.py --run-mode dry-run --target-count 5 --workspace /tmp/signal-engine-nyse-100-acquisition-dry-run

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

build-ir-sec-universe:
	$(PYTHON) scripts/build_nyse_5y_ir_sec_universe.py

build-ir-sec-availability-matrix:
	$(PYTHON) scripts/build_ir_sec_availability_matrix.py

build-ir-sec-permitted-ingest-queue:
	$(PYTHON) scripts/build_ir_sec_permitted_ingest_queue.py

report-manual-local-vs-ir-sec-gap:
	$(PYTHON) scripts/report_manual_local_vs_ir_sec_gap.py

validate-ir-sec-acquisition-policy:
	$(PYTHON) scripts/validate_ir_sec_acquisition_policy.py --path configs/ir_sec_acquisition_policy.example.yml

validate-ir-sec-source-candidates:
	$(PYTHON) scripts/validate_ir_sec_source_candidates.py --path data/corpus/official_ir_candidate_map.yml --path data/corpus/sec_metadata_queue.yml

validate-ir-sec-availability-matrix:
	$(PYTHON) scripts/validate_ir_sec_availability_matrix.py --path reports/agent5/ir_sec_availability_matrix.csv

validate-ir-sec-permitted-ingest:
	$(PYTHON) scripts/validate_ir_sec_permitted_ingest_queue.py --path data/corpus/ir_sec_permitted_ingest_queue.yml

ir-sec-acquisition-check: build-ir-sec-universe build-official-ir-candidate-map build-sec-metadata-queue build-ir-sec-availability-matrix build-ir-sec-permitted-ingest-queue report-manual-local-vs-ir-sec-gap validate-ir-sec-acquisition-policy validate-ir-sec-source-candidates validate-ir-sec-availability-matrix validate-ir-sec-permitted-ingest

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

.PHONY: doctor artifact-manifest-check capstone-ci build-nyse-5y-universe build-official-ir-candidate-map build-sec-metadata-queue build-webcast-metadata-queue build-slides-availability-map build-source-availability-matrix build-permitted-ingest-queue validate-manual-local-sop report-rights-gated-discovery report-500-call-coverage agent5-rights-gated-discovery-check agent5-aggressive-acquisition-check review-rank-queue review-contamination-flags review-calibration-batch review-packets promotion-check training-readiness agent1-validate-registry agent1-speakers agent1-qna-pairs agent1-guidance agent1-review-queue agent1-30-call-pilot evaluation-manifest-check evaluation-sample-gates retrieval-gate-report evaluation-claims-check evaluation-gate-report agent2-evaluation-check manual-local-discovery manual-local-media-discovery retrieval-readiness-30 real-pilot-readiness-check

doctor:
	PYTHONPATH=src $(PYTHON) -m earnings_call_sentiment doctor --json

artifact-manifest-check:
	$(PYTHON) scripts/validate_artifact_manifest.py

build-nyse-5y-universe:
	$(PYTHON) scripts/build_nyse_5y_target_universe.py

build-official-ir-candidate-map:
	$(PYTHON) scripts/build_official_ir_candidate_map.py

build-sec-metadata-queue:
	$(PYTHON) scripts/build_sec_metadata_queue.py

build-webcast-metadata-queue:
	$(PYTHON) scripts/build_webcast_metadata_queue.py

build-slides-availability-map:
	$(PYTHON) scripts/build_slides_availability_map.py

build-source-availability-matrix:
	$(PYTHON) scripts/build_source_availability_matrix.py

build-permitted-ingest-queue:
	$(PYTHON) scripts/build_permitted_ingest_queue.py

validate-manual-local-sop:
	$(PYTHON) scripts/validate_manual_local_sop.py

report-rights-gated-discovery:
	$(PYTHON) scripts/report_rights_gated_discovery.py

report-500-call-coverage:
	$(PYTHON) scripts/report_500_call_coverage.py

agent5-rights-gated-discovery-check: build-nyse-5y-universe build-official-ir-candidate-map build-sec-metadata-queue build-webcast-metadata-queue build-slides-availability-map build-source-availability-matrix build-permitted-ingest-queue validate-manual-local-sop report-rights-gated-discovery report-500-call-coverage

agent5-aggressive-acquisition-check: agent5-rights-gated-discovery-check

review-rank-queue:
	$(PYTHON) scripts/build_first_100_review_queue.py

review-contamination-flags:
	$(PYTHON) scripts/review_flag_contamination.py

review-calibration-batch:
	$(PYTHON) scripts/build_calibration_batch.py

review-packets:
	$(PYTHON) scripts/build_reviewer_packets.py

promotion-check:
	$(PYTHON) scripts/validate_promotion_manifest.py

training-readiness:
	$(PYTHON) scripts/report_training_readiness.py

agent1-validate-registry:
	$(PYTHON) scripts/agent1_validate_manual_local_sources.py

agent1-speakers:
	$(PYTHON) scripts/agent1_assign_speakers.py

agent1-qna-pairs:
	$(PYTHON) scripts/agent1_build_qna_pairs.py

agent1-guidance:
	$(PYTHON) scripts/agent1_guidance_comparator.py

agent1-30-call-pilot: agent1-validate-registry agent1-section agent1-speakers agent1-candidates agent1-dedupe agent1-qna-pairs agent1-guidance agent1-review-queue agent1-error-analysis

evaluation-manifest-check:
	$(PYTHON) scripts/eval/validate_evaluation_manifest.py

evaluation-sample-gates:
	$(PYTHON) scripts/eval/run_sample_gates.py

retrieval-gate-report:
	$(PYTHON) scripts/eval/run_retrieval_gate_report.py

evaluation-claims-check:
	$(PYTHON) scripts/eval/validate_claims.py

evaluation-gate-report:
	$(PYTHON) scripts/eval/build_evaluation_gate_report.py

agent2-evaluation-check: evaluation-manifest-check evaluation-sample-gates retrieval-gate-report evaluation-claims-check evaluation-gate-report

manual-local-discovery:
	$(PYTHON) scripts/discover_manual_local_transcripts.py

manual-local-media-discovery:
	$(PYTHON) scripts/discover_manual_local_media.py

retrieval-readiness-30:
	$(PYTHON) scripts/build_agent1_retrieval_objects.py

capstone-ci:
	$(PYTHON) -m py_compile $$(find scripts src tools -name "*.py")
	$(PYTHON) -m pytest
	@if command -v ruff >/dev/null 2>&1; then ruff check .; elif [ -x "$(RUFF)" ]; then "$(RUFF)" check .; else echo "ruff unavailable; skipped"; fi
	$(MAKE) corpus-safe-check
	$(MAKE) training-plan-check
	$(MAKE) gold-audit
	$(MAKE) first-100-review-queue
	$(MAKE) agent1-pilot
	$(MAKE) restricted-artifacts-check
	@if [ -f scripts/check_markdown_links.py ]; then $(PYTHON) scripts/check_markdown_links.py; else echo "markdown link checker unavailable; skipped"; fi

real-pilot-readiness-check: doctor artifact-manifest-check agent5-rights-gated-discovery-check review-rank-queue review-contamination-flags review-calibration-batch review-packets promotion-check training-readiness agent1-30-call-pilot agent2-evaluation-check manual-local-discovery manual-local-media-discovery retrieval-readiness-30

.PHONY: discover-approved-local-transcripts build-manual-local-batch build-gold-provenance-repair manual-actions-training-unlock agent1-candidate-readiness manual-local-registration-check

discover-approved-local-transcripts:
	$(PYTHON) scripts/discover_approved_local_transcripts.py

build-manual-local-batch:
	$(PYTHON) scripts/build_manual_local_batch_from_discovery.py

build-gold-provenance-repair:
	$(PYTHON) scripts/build_gold_provenance_repair_candidates.py

manual-actions-training-unlock:
	$(PYTHON) scripts/report_manual_actions_to_unlock_training.py

agent1-candidate-readiness:
	$(PYTHON) scripts/report_agent1_candidate_generation_readiness.py

manual-local-registration-check: discover-approved-local-transcripts build-manual-local-batch validate-manual-local-registry build-gold-provenance-repair manual-actions-training-unlock agent1-candidate-readiness

rights-check: registry-check claims-check restricted-artifacts-check

corpus-safe-check: rights-check corpus-manifest-check retrieval-schema-check event-study-check training-plan-check benchmark-sanity-check nyse-universe-check source-discovery-check manual-local-check media-registration-check retrieval-build-check nlp-training-sources-check experiment-design-check event-study-join-check agent5-acquisition-check promotion-manifest-check

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

NYSE_DESKTOP_WORKSPACE ?= /Users/keith/Desktop/earnings calls 100 samples

.PHONY: free-local-ingestion-check user-authorized-permitted-downloads user-authorized-download-assets register-user-authorized-assets normalize-registered-transcripts build-event-chunks validate-event-chunks export-retrieval-objects build-audio-rag retrieval-readiness operational-ingestion-summary operational-ingestion-check

free-local-ingestion-check:
	$(PYTHON) tools/build_operational_ingest_baseline.py --workspace "$(NYSE_DESKTOP_WORKSPACE)"
	$(PYTHON) scripts/validate_user_authorized_ingest.py --workspace "$(NYSE_DESKTOP_WORKSPACE)" || true

user-authorized-permitted-downloads:
	$(PYTHON) tools/build_user_authorized_permitted_downloads.py --queue data/acquisition/nyse_100_source_rights_review_queue.csv --policy configs/nyse_100_user_authorized_ingest_policy.yml --out data/acquisition/nyse_100_user_authorized_permitted_downloads.csv --desktop-out "$(NYSE_DESKTOP_WORKSPACE)/_audit/user_authorized_permitted_downloads.csv" --workspace "$(NYSE_DESKTOP_WORKSPACE)"

user-authorized-download-assets:
	$(PYTHON) tools/download_user_authorized_earnings_assets.py --manifest data/acquisition/nyse_100_user_authorized_permitted_downloads.csv --policy configs/nyse_100_user_authorized_ingest_policy.yml --workspace "$(NYSE_DESKTOP_WORKSPACE)"

register-user-authorized-assets:
	$(PYTHON) tools/register_user_authorized_desktop_assets.py --workspace "$(NYSE_DESKTOP_WORKSPACE)" --download-log "$(NYSE_DESKTOP_WORKSPACE)/_audit/user_authorized_download_log.csv"
	$(PYTHON) scripts/validate_manual_local_registries.py --workspace "$(NYSE_DESKTOP_WORKSPACE)"

normalize-registered-transcripts:
	$(PYTHON) tools/normalize_registered_transcripts.py --registry data/corpus/manual_local_transcript_registry.csv --workspace "$(NYSE_DESKTOP_WORKSPACE)"

build-event-chunks:
	$(PYTHON) tools/build_event_chunks.py --registry data/corpus/manual_local_transcript_registry.csv --workspace "$(NYSE_DESKTOP_WORKSPACE)"

validate-event-chunks:
	$(PYTHON) tools/validate_chunk_manifest.py

export-retrieval-objects:
	$(PYTHON) tools/export_retrieval_objects.py --chunk-manifest data/acquisition/nyse_100_chunk_manifest.csv --out data/retrieval/retrieval_objects_manifest.csv

build-audio-rag:
	$(PYTHON) tools/build_user_authorized_audio_rag.py --registry data/corpus/manual_local_audio_registry.csv --workspace "$(NYSE_DESKTOP_WORKSPACE)"
	$(PYTHON) tools/run_local_asr.py --registry data/corpus/manual_local_audio_registry.csv

retrieval-readiness:
	$(PYTHON) tools/build_local_retrieval_index.py --objects data/retrieval/retrieval_objects_manifest.csv --out .local/signal_engine/retrieval/indexes/nyse100_bm25
	$(PYTHON) tools/evaluate_retrieval.py --index .local/signal_engine/retrieval/indexes/nyse100_bm25 --queries data/retrieval/eval_queries.example.jsonl

operational-ingestion-summary:
	$(PYTHON) tools/build_operational_ingestion_summary.py --workspace "$(NYSE_DESKTOP_WORKSPACE)"

operational-ingestion-check: free-local-ingestion-check user-authorized-permitted-downloads register-user-authorized-assets normalize-registered-transcripts build-event-chunks validate-event-chunks export-retrieval-objects build-audio-rag retrieval-readiness operational-ingestion-summary
	$(PYTHON) scripts/validate_user_authorized_ingest.py --workspace "$(NYSE_DESKTOP_WORKSPACE)"
