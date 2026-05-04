# Transcript Downloader And Corpus Pipeline

Local-first tooling for the Signal Engine transcript corpus. The raw `raw/transcript.txt` file is canonical and must not be edited by cleaning, audit, or analysis steps.

## Install

```bash
python3 -m pip install requests beautifulsoup4 pypdf pyyaml
```

The repository already includes the broader Signal Engine dependencies in `pyproject.toml`.

## Download

```bash
python tools/transcript_downloader/download_transcripts.py \
  --out "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
```

Edit `tools/transcript_downloader/sources.yaml` to add or update public sources. Use official investor relations PDF transcripts when available. If no public PDF exists, use a reputable full transcript HTML page. Do not add paywalled, login-protected, blocked, or robots-disallowed sources.

## Audit

```bash
python tools/transcript_downloader/audit_transcripts.py \
  --root "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
```

Audit outputs are written to the corpus root:

- `transcript_quality_audit.csv`
- `transcript_quality_audit.md`
- `duplicate_transcripts.csv`

Warnings include missing transcripts, short transcripts, missing Operator or Q&A markers, repeated navigation text, and blocked/login/paywall markers.

Warning review outputs may be written locally as:

- `audit_warning_review.csv`
- `audit_warning_review.md`

Use these to distinguish real quality issues from cosmetic source boilerplate, expected source-format limitations, and tooling false positives. Do not suppress a warning unless the review evidence shows it is cosmetic or false positive.

## Analyze

```bash
python tools/transcript_downloader/run_corpus_analysis.py \
  --root "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
```

The analysis runner creates a timestamped backup before corpus mutations, removes the user-specified excluded case from the active corpus, hashes raw transcripts before and after processing, and fails the report if any active raw transcript hash changes.

Only audited, complete, non-quarantined cases are analyzed. Quarantined cases are moved under `quarantine/` and excluded from analysis.

## Folder Structure

```text
{CASE_ID}/
  raw/
    transcript.txt
    transcript.pdf optional
  clean/
    transcript_clean.txt
    transcript_cleaning_report.json
  sections/
    prepared_remarks.txt
    q_and_a.txt
    unknown.txt
  speakers/
    speaker_turns.jsonl
  labels/
    weak_labels.jsonl
    gold_labels.jsonl optional
  analysis/
    signals.json
    guidance.json
    top_signals.md
    error_analysis.md optional
  demo/
    demo_summary.md
  metadata.json
```

## Gold Labels

Starter gold-label files are created for selected cases. Add human-reviewed JSONL rows only after checking exact character spans in the canonical raw transcript or derived clean transcript.

Suggested row shape:

```json
{"type":"guidance_revision","text_span":"...","start_char":0,"end_char":0,"reviewer":"...","rationale":"..."}
```

Do not fake labels. Use at least 5-10 reviewed labels per selected case before treating evaluation outputs as meaningful.

Validate gold-label scaffolds with:

```bash
python tools/transcript_downloader/validate_gold_labels.py \
  --root "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
```

Empty scaffold files are reported as `needs_human_labeling`. The validator never converts weak labels into gold labels.

Label evaluation is scaffold-only until human gold labels exist. Weak-label counts are not accuracy, precision, recall, or F1.

## Outputs

Global outputs include corpus manifests, size reports, analysis summaries, baseline comparison, validation reports, raw hash manifests, runtime logs, and demo corpus summaries. Per-case demo summaries live under `{CASE_ID}/demo/demo_summary.md`.
