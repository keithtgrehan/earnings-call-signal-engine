# SEC EDGAR Intake Guide

SEC intake is metadata-only in this scaffold. It helps identify candidate filings but does not download transcripts, exhibits, PDFs, audio, video, or paid/API outputs.

## Tool

Use `scripts/fetch_sec_8k_index.py` only when you have a valid SEC user agent.

Example:

```bash
python scripts/fetch_sec_8k_index.py --ticker NVDA --user-agent "Keith Grehan keith@example.com" --limit 5 --json-out /tmp/nvda_8k.json
```

## Boundaries

- User agent is required.
- Save only small filing metadata JSON/CSV.
- Do not scrape transcript vendors.
- Do not fetch filing bodies or exhibits as part of this scaffold.
- Treat metadata as source discovery, not validated corpus data.

## Promotion

A filing can become a corpus candidate only after manual review confirms relevance, source rights, transcript availability, and whether the filing actually supports an earnings-call evaluation case.
