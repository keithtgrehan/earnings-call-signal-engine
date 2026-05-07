# Manual Transcript Source Workflow

Use this workflow when a transcript is legally public, but automated URL verification cannot fetch it because of robots.txt, blocking, or a source format an operator has manually saved as plaintext.

This workflow does not bypass robots.txt, scrape blocked pages, or create labels. It only prepares provenance-backed sources for intake and human review.

## How to fill the template

Start from `data/corpus/manual_source_template.csv`.

Required columns:

- `case_id`, `ticker`, `company_name`, `fiscal_year`, `quarter`
- `source_url` when available
- `local_file_path` only when an operator manually saved a public/legal transcript as `.txt` or `.md`
- `source_type`, usually `txt`, `md`, or `html` for URL rows
- `source_license_notes`, required and nonempty
- `public_source_confirmed`, required as `true` before intake
- `notes`, optional reviewer context

For local files, keep the original file outside generated corpus outputs until intake copies it into the immutable case folder.

## Acceptable sources

- Company investor relations transcript pages or transcript PDFs manually converted to plaintext.
- SEC exhibits when the exhibit contains the transcript.
- Other clearly public transcript pages where the source terms allow manual use.
- Plaintext files saved from a public/legal source with source URL and license/provenance notes recorded.

## Unacceptable sources

- Paywalled, login-gated, private, or subscription-only transcripts.
- Captcha, blocked, or robots-disallowed pages fetched by automation.
- Copied transcripts without a public/legal source URL or license note.
- Local files without `public_source_confirmed=true`.
- Local files without source/license notes.

## Prepare sources

```bash
make prepare-manual-transcript-sources
```

This writes:

- `data/corpus/high_signal_source_urls.csv` for verified URL rows
- `data/corpus/manual_transcript_file_manifest.csv` for validated local plaintext files
- `reports/manual_source_validation.md` with accepted and rejected rows

URL rows still go through robots and public-source verification. Local-file rows are validated for transcript length, earnings-call markers, and speaker or section structure.

## Intake local transcript files

```bash
make intake-manual-transcript-files
```

For each accepted local file, intake:

- copies the plaintext into `data/corpus/high_signal_cases/{CASE_ID}/raw/transcript.txt`
- preserves the original local file path in `metadata/provenance.json`
- records `web_downloaded: false`
- stores source/license notes
- generates processed transcript files, weak-label suggestions, parse reports, and human labeling packets

Raw transcript files are not overwritten unless the operator explicitly passes `--overwrite true`.

## Review and promotion

```bash
make review-after-manual-intake
```

Weak labels are suggestions only. A human reviewer must mark `reviewer_decision` as `accept`, `reject`, or `unclear`.

Only after accepted decisions are present:

```bash
make promote-reviewed-priority-labels
make eval-after-review
```

No gold labels are created by manual source preparation or intake.
