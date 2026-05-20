# Tiered Transcript Acquisition Workflow

This workflow finds and acquires legally usable public earnings-call transcripts for Tier 1-4 target cases when automated access is allowed.

It is deterministic and reviewable. It does not crawl the web, bypass robots.txt, scrape blocked pages, use paywalled/private sources, or promote labels.

## What is automated

- Read configured Tier 1-4 target cases from `data/corpus/tiered_transcript_targets.csv`.
- Expand approved exact URL patterns and imported candidate URL files.
- Check robots.txt before any source verification.
- Verify HTTP status, content type, block/paywall markers, transcript markers, ticker/company consistency, fiscal period consistency, and acquisition quality.
- Acquire only verified, robots-allowed HTML/plaintext transcript candidates.
- Normalize acquired HTML/plaintext to UTF-8 text under ignored local manual-source paths.
- Write provenance manifests and reports.

## What is intentionally not automated

- No uncontrolled crawling.
- No broad scraping.
- No autonomous search-engine traversal.
- No hidden search dependencies.
- No paywalled, private, login-gated, captcha, or blocked sources.
- No PDF parsing.
- No OCR.
- No embeddings or retrieval.
- No gold-label creation or promotion.
- No investment, trading, or performance claims.

## Deterministic Acquisition Policy

Discovery and acquisition must not use:

- LLM summarization
- LLM extraction
- LLM classification
- autonomous agents
- hidden AI preprocessing
- AI-assisted verification

LLMs may later assist separate review, synthesis, retrieval benchmarking, or analyst workflows. They must never be used for acquisition, source verification, provenance, transcript normalization, or safety gating.

Rationale:

- reproducibility
- auditability
- hallucination prevention
- deterministic provenance

## Source rules

Allowed V1 discovery inputs:

- approved URL patterns
- company investor relations pages
- SEC/EDGAR references
- manually supplied URLs
- imported search-result CSV/JSON
- transcript manifests

Disallowed V1 discovery inputs:

- uncontrolled web crawling
- broad scraping
- autonomous search-engine traversal
- hidden search dependencies

Every discovered source preserves:

- source URL
- discovery method
- timestamp
- source type
- validation status

## PDF handling

PDFs are never automatically converted.

PDF candidates are written to `data/corpus/pdf_manual_conversion_queue.csv` and to the manual fallback report. Status values:

- `verified_manual_pdf`
- `blocked_pdf`
- `unsupported_pdf`

Manual conversion can happen later outside this automated workflow, with public-source confirmation and source/license notes.

## Run by tier

All tiers:

```bash
make acquire-tiered-transcripts
```

Discovery only:

```bash
python tools/discover_transcript_sources.py --tiers 1 2
```

Acquisition only:

```bash
make acquire-verified-transcripts
```

Manual file intake after acquisition:

```bash
make prepare-manual-transcript-sources
make intake-manual-transcript-files
```

## Inspect results

- `data/corpus/discovered_transcript_sources.csv`
- `data/corpus/manual_source_template.csv`
- `data/corpus/manual_transcript_file_manifest.csv`
- `data/corpus/pdf_manual_conversion_queue.csv`
- `reports/transcript_source_discovery.md`
- `reports/transcript_acquisition_report.md`
- `reports/manual_transcript_fallback_required.md`

## Commit metadata only

Do not commit transcript bodies or generated label packets.

Before committing:

```bash
python tools/check_no_transcript_text_staged.py
git diff --cached --name-only | grep -E "raw/transcript.txt|processed/|labels/" && exit 1 || echo "No transcript text staged"
```

Expected committed artifacts are configs, manifests, reports, docs, and tests. Raw transcript text remains local and ignored.
