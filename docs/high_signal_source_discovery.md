# High-Signal Source Discovery

`tools/discover_high_signal_transcript_sources.py` finds and verifies public earnings-call transcript URLs for the high-signal benchmark intake set. It writes a source URL CSV that can be passed directly to `tools/intake_high_signal_transcripts.py --source-url-file`.

No transcripts are saved by default, no gold labels are created, and unresolved cases are left unresolved.

## Public-Source Constraints

The discovery tool is intentionally conservative:

- It accepts public HTML, PDF, or plain-text transcript candidates only.
- It checks `robots.txt` before downloading a candidate URL.
- It uses a polite `User-Agent` and rate limits verification requests.
- It rejects paywall, login, captcha, subscription, access-denied, and blocked-page markers.
- It writes candidate evidence and rejection reasons for audit.
- It does not silently scrape private or paywalled sources.

## Query-Only Workflow

Use this first when no search export exists:

```bash
make discover-high-signal-sources-query-only
```

This writes:

```text
data/corpus/high_signal_source_queries.csv
```

The file contains precise search queries for each target case. It does not verify URLs or write source/candidate/report outputs.

## Search-Results-File Workflow

Export search results from Google, Bing, Tavily, SerpAPI, or manual research to CSV or JSON, then run:

```bash
python tools/discover_high_signal_transcript_sources.py \
  --search-results-file data/corpus/high_signal_search_results.csv
```

Accepted URL columns include `source_url`, `url`, `link`, or `href`. Rows should include `case_id`, or the trio `ticker`, `fiscal_year`, and `quarter`.

## Verify-Only Workflow

To verify a manually curated candidate URL file:

```bash
python tools/discover_high_signal_transcript_sources.py \
  --verify-only \
  --source-url-file data/corpus/high_signal_candidate_urls.csv
```

The same CSV/JSON parsing rules apply. Live search is not required.

## Output Schemas

Selected verified source URLs are written to:

```text
data/corpus/high_signal_source_urls.csv
```

Schema:

`case_id`, `ticker`, `company_name`, `fiscal_year`, `quarter`, `source_url`, `source_type`, `source_domain`, `confidence`, `verification_status`, `transcript_char_estimate`, `matched_markers`, `notes`

All accepted, rejected, blocked, paywalled, robots-disallowed, and failed candidates are written to:

```text
data/corpus/high_signal_source_candidates.json
```

The report is written to:

```text
reports/high_signal_source_discovery.md
```

It summarizes target calls, already resolved sources, newly verified sources, still-missing cases, blocked/paywalled cases, top verified domains, and manual review needs.

## Intake Integration

After verification:

```bash
make intake-high-signal-from-discovered-sources
```

Equivalent direct command:

```bash
python tools/intake_high_signal_transcripts.py \
  --source-url-file data/corpus/high_signal_source_urls.csv \
  --years 2024 2025 2026 \
  --quarters Q1 Q2 Q3 Q4 \
  --output-root data/corpus/high_signal_cases \
  --max-cases-per-ticker 4
```

Discovery only validates candidate public URLs. Intake downloads and parses verified sources into the transcript corpus structure.

## Limitations

- Search is provider-agnostic and defaults to local/manual workflows. If no supported search export or candidate URL file is supplied, the tool fails clearly.
- Optional live search does not require paid APIs and is not used unless explicitly requested and configured.
- Verification is deterministic but conservative. Some legitimate transcripts may remain candidates until manually reviewed.
- The tool does not create transcripts unless `--cache-sources` is explicitly set, and cached source pages are for audit only.
- No gold labels are created or promoted. Human review remains the only path to label promotion.
