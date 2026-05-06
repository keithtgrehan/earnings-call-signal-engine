# High-Signal Transcript Intake

This workflow prepares legally sourced, provenance-tracked earnings-call transcripts for future human review. It expands the real transcript corpus while keeping deterministic transcript-first analysis canonical.

No gold labels are auto-created. Weak labels are suggestions only.

## Ticker List

The high-signal expansion set is:

`TSLA`, `AMD`, `CRM`, `SNOW`, `HUBS`, `NOW`, `DDOG`, `NET`, `MDB`, `PANW`, `CRWD`, `SHOP`, `UBER`, `RBLX`, `COIN`, `ASML`, `TSM`.

## Commands

Dry run:

```bash
python tools/intake_high_signal_transcripts.py \
  --tickers TSLA AMD CRM SNOW HUBS NOW DDOG NET MDB PANW CRWD SHOP UBER RBLX COIN ASML TSM \
  --years 2024 2025 2026 \
  --quarters Q1 Q2 Q3 Q4 \
  --output-root data/corpus/high_signal_cases \
  --max-cases-per-ticker 4 \
  --dry-run
```

Live intake:

```bash
make intake-high-signal-transcripts
```

The live command uses configured public sources when available and writes manual-provenance placeholders when no supported public source is configured.

## Folder Structure

Each case is organized as:

```text
data/corpus/high_signal_cases/{TICKER}_{YEAR}_{QUARTER}/
  raw/
    transcript.txt
    source.html or transcript.pdf
  metadata/
    provenance.json
    source_url.txt
  processed/
    transcript_sectioned.json
    transcript_clean.txt
  labels/
    human_labeling_packet.md
    weak_label_candidates.jsonl
  outputs/
    intake_status.json
    parse_report.md
```

The manifest files are:

- `data/corpus/high_signal_cases/high_signal_manifest.csv`
- `data/corpus/high_signal_cases/high_signal_manifest.json`

## Validation Rules

A transcript is review-ready only when:

- `raw/transcript.txt` exists.
- character count is at least `--min-transcript-chars`.
- earnings-call markers are present when `--require-markers` is enabled.
- speaker structure or section markers are plausible.
- no login, paywall, captcha, or blocked-page marker is detected.

Invalid or warning cases still receive provenance and status files when a case folder is created, but they are not marked review-ready.

## Parsing Behavior

The parser is intentionally conservative. It separates prepared remarks and Q&A when obvious section markers exist, extracts speaker turns when lines look like `Speaker Name: text`, and otherwise stores section-level text with warnings. It does not mutate raw transcripts.

## Weak Labels

When deterministic weak-label logic is available, the intake tool writes candidate suggestions to `labels/weak_label_candidates.jsonl` and summarizes the top candidates in `labels/human_labeling_packet.md`.

These rows are not gold labels. A human reviewer must accept or correct evidence spans before any promotion to `data/gold/gold_labels.jsonl`.

## Manifest Fields

The committed manifest records:

`case_id`, `ticker`, `year`, `quarter`, `status`, `source_url`, `transcript_chars`, `has_raw`, `has_processed`, `has_packet`, `review_ready`, `quality_flags`.

## What This Achieves

- Expands transcript intake in a reproducible, provenance-backed way.
- Makes review packets available next to each valid transcript.
- Separates raw transcripts, parsed outputs, weak-label suggestions, and status reports.
- Supports future growth from 57 gold labels toward 100+ reviewed labels.

## What This Does Not Achieve

- It does not create synthetic labels.
- It does not promote weak labels into gold labels.
- It does not use paywalled/private sources.
- It does not make trading, market-alpha, production-ML, or statistical-significance claims.
- It does not validate retrieval or multimodal intelligence.
