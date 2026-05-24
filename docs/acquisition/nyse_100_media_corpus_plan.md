# NYSE 100 Media Corpus Plan

## Goals

Build a local, rights-aware workspace for at least 100 recent NYSE earnings-call candidate cases at:

`/Users/keith/Desktop/earnings calls 100 samples`

The workspace is transcript-first. Audio and video references are support layers for later human review, timing checks, or selective multimodal audit. The default run creates folders, metadata manifests, provenance records, source registries, availability summaries, and manual-review queues. It does not download or store raw transcript bodies, audio, video, slides, webcast files, or vendor content.

## Legal And Technical Constraints

- NYSE-listed companies only.
- Maximum lookback is 5 years.
- Recent calls are prioritized before older calls.
- Unknown source rights fail closed.
- No authentication, paywall, robots policy, DRM, signed URL, session, or vendor restriction bypass.
- No raw transcript, audio, video, slides, or copyrighted media in git.
- No vendor raw ingest unless a license config explicitly permits the requested storage and use.
- YouTube links and metadata may be indexed, but YouTube audio/video acquisition remains blocked unless explicit authorization exists.
- SEC/EDGAR is metadata-first and must use fair-access behavior before any live metadata fetch is enabled.
- Official IR raw acquisition requires source-specific source-terms review, robots review, and explicit approval flags.
- Manual-local files remain registered by operator-supplied path and sha256 hash only.
- No live execution, portfolio, causal, or statistical-strength claims are created by this corpus workflow.

## Discovery Philosophy

The workflow indexes the broadest safe set of candidate sources first, then separates cases by availability and rights tier. It prefers links and metadata over risky downloads. Every candidate can be useful as a review target even when raw acquisition is blocked.

The first run is intentionally metadata-only. Priority tiers only improve after a human or rights-reviewed automated process confirms that the transcript, audio, or video source is available and permitted.

## Source Ranking

1. Company investor-relations pages.
2. Official webcast providers linked from company IR.
3. SEC/EDGAR event metadata and exhibit metadata.
4. Public transcript providers where access and terms permit use.
5. Public webcast replay pages.
6. YouTube metadata references only.
7. Other public metadata sources.

## Folder Structure

Company folder:

`/Users/keith/Desktop/earnings calls 100 samples/{TICKER}_{COMPANY_NAME}/`

Call folder:

`/Users/keith/Desktop/earnings calls 100 samples/{TICKER}_{COMPANY_NAME}/{YYYY-MM-DD}_FY{YYYY}_{Q}/`

Each call folder contains:

- `transcript/`
- `audio/`
- `video/`
- `metadata/`
- `provenance/`

The default run writes only JSON metadata and provenance files inside `metadata/` and `provenance/`. The media folders are placeholders for later approved local acquisition.

## Metadata Schema

The manifest has one row per candidate call. Required fields are:

- `case_id`
- `ticker_symbol`
- `company_name`
- `exchange`
- `fiscal_year`
- `fiscal_quarter`
- `calendar_year`
- `earnings_call_date`
- `transcript_source_url`
- `audio_source_url`
- `video_source_url`
- `transcript_availability`
- `audio_availability`
- `video_availability`
- `source_type`
- `rights_status`
- `priority_tier`
- `local_paths_created`
- `notes`
- `source_domain`
- `discovered_timestamp`
- `acquisition_method`
- `provenance_hash`
- `call_folder`

Allowed availability values:

- `available`
- `unavailable`
- `blocked`
- `paywalled`
- `unknown`

Allowed source types:

- `company_ir`
- `sec_edgar`
- `webcast_provider`
- `earnings_platform`
- `youtube_metadata_only`
- `investor_platform`
- `other`

Allowed rights statuses:

- `safe_to_link`
- `safe_to_download`
- `metadata_only`
- `blocked`
- `unknown`

Allowed priority tiers:

- `1`: transcript, audio, and video available.
- `2`: transcript and audio available.
- `3`: transcript available.
- `4`: metadata-only, blocked, unknown, or incomplete.

## Blocked-Source Handling

Blocked sources are retained as metadata rows when legally useful for planning. They must include:

- source type
- source URL or non-fetch reference
- source domain
- blocked reason
- manual action
- provenance hash

Blocked rows must not trigger downloads. They exist to make the next human review step explicit.

## Metadata-Only Behavior

Metadata-only mode:

- creates the local folder skeleton
- writes `metadata/manifest.json`
- writes `provenance/provenance.json`
- writes repo-level manifest and source registry CSV files
- writes progress and status reports
- leaves transcript/audio/video folders empty
- keeps all raw download flags false

## Provenance Requirements

Every manifest row and source-registry row has a sha256-prefixed provenance hash. The hash covers stable identifying fields such as case ID, ticker, company, fiscal period, source URL/reference, rights status, and acquisition method. Manual-local follow-up must add operator-supplied path and sha256 hash for any local raw file, without copying that file into git.

## Validation Workflow

Run:

```bash
python scripts/validate_nyse_100_media_manifest.py
pytest tests/test_validate_nyse_100_media_manifest.py tests/test_discover_nyse_earnings_media.py -q
```

The validator enforces:

- exchange equals NYSE
- dates are within 5 years and not in the future
- ticker, company, fiscal period, and call date are present
- available media statuses have source URLs
- priority, rights, source type, and availability enums are valid
- local folder skeleton exists
- manifest rows are unique
- blocked or paywalled availability is explicitly noted
- repo-tracked raw media paths are rejected

## Human-Review Workflow

1. Review company IR terms and robots policy for the top official IR domains.
2. Confirm whether transcript pages, webcast replay pages, slides, or event pages permit the intended local use.
3. If rights are unclear, use manual-local registration after the operator supplies a local path, sha256 hash, and rights context.
4. Use SEC/EDGAR metadata to identify likely 8-Ks, releases, dates, exhibits, and event timing. Do not assume SEC provides full earnings-call transcripts.
5. Keep YouTube as metadata and links only unless explicit authorization exists.
6. Register any vendor source only after license configuration exists.

## Scaling Path Toward 500 Calls

The current tool can create a 100-call target set from the seed universe by walking recent fiscal quarters first. Scaling to 500 calls should:

- expand the NYSE company universe with exchange-verified targets
- add a reviewed official IR domain registry
- add optional SEC metadata fetch with a descriptive User-Agent and a hard <=10 requests/second cap
- preserve network-disabled defaults in tests
- keep transcript bodies canonical only after rights are reviewed
- keep audio/video as support layers
- promote cases by manifest updates rather than by copying raw assets into git
