# Control Room Codex Rollout Review

## What Changed

This rollout adds a rights-cleared resource/corpus/evaluation readiness layer without acquiring new data.

Artifacts:

- `schemas/*resource*`, corpus, training, external dataset, retrieval, and event-study schemas;
- `configs/resource_registry.example.yml`;
- metadata-only data source adapters;
- registry builder and validator;
- restricted-artifact checker;
- separated training-candidate exporter;
- corpus/resource dashboard;
- claims matrix validator.

## Control Room Checks

1. Build starter registry:
   `python scripts/build_resource_registry.py --config configs/resource_registry.example.yml`
2. Validate registry:
   `python scripts/validate_resource_registry.py --path configs/resource_registry.example.yml`
3. Check staged artifacts:
   `python scripts/check_restricted_artifacts.py --staged`
4. Export separated candidates:
   `python scripts/export_training_candidates.py`
5. Validate claims:
   `python scripts/validate_claims_matrix.py --path configs/claims_matrix.example.yml`
6. Build dashboard:
   `python scripts/build_corpus_status_dashboard.py --registry configs/resource_registry.example.yml`

## Rollout Decision

Safe to use as scaffold. Not a data acquisition run. Not permission to copy restricted transcripts. Not permission to train on external or weak labels.

## Stop Conditions

- missing or unknown `rights_tier`;
- missing provenance hash;
- raw transcript/audio/video path without explicit allowed raw-body commit;
- paywall/login/vendor source without explicit license;
- external dataset rows being promoted to gold;
- claims of alpha, live trading, or statistical significance.
