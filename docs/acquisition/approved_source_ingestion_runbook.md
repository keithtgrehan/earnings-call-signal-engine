# Approved Source Ingestion Runbook

This runbook starts after the source-rights review queue exists. It keeps raw transcripts, audio, video, ASR text, embeddings, and vector stores out of git.

## Operator Flow

1. Build or refresh the fail-closed review queue.

```bash
python tools/build_source_rights_review_queue.py
python scripts/validate_source_rights_review_queue.py
```

2. Prioritize the next rows for manual source-rights review.

```bash
python tools/prioritize_source_rights_queue.py
```

Outputs:

- `reports/acquisition/source_rights_priority_summary.md`
- `reports/acquisition/source_rights_priority_summary.json`

3. Copy reviewed queue rows into the approval template and fill only reviewed approvals.

```bash
cp configs/nyse_100_source_approval_template.csv /tmp/nyse_100_source_approvals.csv
```

Required for any `allow_download=true` row:

- `rights_status` is `safe_to_download` or `rights_cleared`
- `approval_ref`
- `approved_by`
- `approved_at`
- `source_terms_checked=true`
- `robots_checked=true`
- `commit_allowed=false`

Training use additionally requires `explicit_training_rights_ref`.

4. Validate the approval CSV before promotion.

```bash
python scripts/validate_nyse_100_source_approvals.py --input /tmp/nyse_100_source_approvals.csv
```

5. Promote approved rows into the permitted-download manifest.

```bash
python tools/apply_manual_source_approvals.py \
  --input /tmp/nyse_100_source_approvals.csv \
  --out data/acquisition/nyse_100_permitted_downloads.csv
```

6. Dry-run acquisition before any permitted run.

```bash
python tools/acquire_nyse_100_assets.py \
  --run-mode dry-run \
  --workspace /tmp/signal-engine-nyse-100-acquisition-dry-run \
  --target-count 5
```

7. Run permitted-only acquisition only after approvals are validated.

```bash
python tools/acquire_nyse_100_assets.py \
  --run-mode permitted-only \
  --manual-approvals data/acquisition/nyse_100_permitted_downloads.csv \
  --workspace "/Users/keith/Desktop/earnings calls 100 samples"
```

## Manual Local Assets

Use manual-local registration when the operator already has a reviewed local transcript or audio file. The tool records path, hash, approval, and provenance metadata only. It does not copy raw files into the repo.
Rows marked `manual_local_review_only` can be registered here, but they do not unlock external download promotion.

Create a local path map CSV with:

```csv
case_id,ticker,asset_type,source_url,local_path,raw_git_committed
jpm_2025_q4,JPM,transcript,https://ir.example.com/transcript,/Users/keith/Desktop/approved/jpm_q4.txt,false
```

Then run:

```bash
python tools/register_manual_local_assets.py \
  --approvals /tmp/nyse_100_source_approvals.csv \
  --path-map /tmp/manual_local_asset_paths.csv \
  --out data/acquisition/manual_local_asset_registry.csv
```

Outputs:

- `data/acquisition/manual_local_asset_registry.csv`
- `reports/acquisition/manual_local_asset_registration.md`
- `reports/acquisition/manual_local_asset_registration.json`

## Validation

```bash
python -m py_compile \
  tools/acquire_nyse_100_assets.py \
  tools/apply_manual_source_approvals.py \
  tools/build_source_rights_review_queue.py \
  tools/build_nyse_100_audio_rag_manifest.py \
  tools/build_nyse_100_rag_chunks.py \
  tools/source_rights_common.py \
  scripts/validate_nyse_100_asset_acquisition.py \
  scripts/validate_source_rights_review_queue.py \
  scripts/validate_nyse_100_chunk_manifest.py \
  scripts/validate_nyse_100_source_approvals.py \
  tools/register_manual_local_assets.py \
  tools/prioritize_source_rights_queue.py
```

```bash
git ls-files | grep -Ei '\.(mp3|wav|m4a|aac|flac|ogg|mp4|mov|mkv|webm|avi)$' || true
git grep -n '<<<<<<<\|=======\|>>>>>>>' README.md AGENTS.md configs docs scripts src tests tools || true
```

## Guardrails

- Unknown, restricted, blocked, and metadata-only rights fail closed for raw download.
- YouTube media download is blocked.
- Vendor raw ingest requires `license_config_ref`.
- `commit_allowed` must remain false.
- Raw local files must stay outside the git repo unless they are under an explicitly allowed ignored local workspace.
- Downloads remain disabled by default in example policy.
- ASR, embeddings, vector DB creation, and model training stay out of this workflow.

## Non-Goals

- No raw transcript/audio/video commit.
- No paywall, login, robots, vendor, or source-terms bypass.
- No YouTube media download.
- No ASR text generation or commit.
- No embeddings or vector DB.
- No training dataset promotion.
- No trading, alpha, causal, or statistical-significance claims.
