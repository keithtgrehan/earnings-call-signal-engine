# Acquisition Quality Scoring

Acquisition quality scoring is a deterministic pre-intake check for public earnings-call transcript candidates. It helps separate sources that are ready for automated plaintext intake from sources that need manual review or conversion.

The score is not a signal-quality metric and is not an investment or trading claim. It only describes source suitability for transcript acquisition.

## Bands

- `high`: score `>= 80`
- `medium`: score `>= 60` and `< 80`
- `low`: score `>= 40` and `< 60`
- `unusable`: score `< 40`, or any hard failure

Hard failures force `unusable`:

- robots-disallowed
- blocked, paywalled, login, captcha, or gated source
- unsupported content type
- failed download
- invalid URL

PDFs are scored as metadata-only manual conversion candidates. They are not parsed, OCRed, or automatically converted.

## Scoring Inputs

Positive deterministic signals:

- transcript length
- prepared remarks markers
- Q&A markers
- speaker labels
- clean UTF-8 normalization
- ticker or company match
- fiscal year or quarter match
- no obvious duplicate/repetition signal

Negative deterministic signals:

- blocked or paywalled text markers
- unsupported content type
- short transcript text
- weak ticker/company match
- repetitive or duplicate-looking body text

## Examples

High-quality candidate:

- long HTML or plaintext transcript
- contains `Prepared remarks`
- contains `Question-and-Answer` or `Q&A`
- has speaker labels such as `Operator:` and `Analyst:`
- matches ticker/company and fiscal period
- clean UTF-8 text

Low-quality candidate:

- short article or event page
- weak or missing Q&A structure
- missing speaker labels
- partial company match only
- repetitive boilerplate or navigation text

Unusable candidate:

- robots-disallowed
- login/paywall/captcha marker
- unsupported file type
- failed download
- PDF body that would require parsing or OCR

## Why this matters

Evaluation quality depends on source quality. A clean, complete transcript can produce stable evidence spans and reliable review packets. Weak or partial source text can create misleading weak labels, noisy review queues, and brittle benchmark results.

Quality scoring happens before evaluation so the repo can preserve source provenance, route questionable material to manual review, and keep deterministic transcript-first outputs canonical.
