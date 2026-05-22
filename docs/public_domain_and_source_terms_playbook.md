# Public Domain and Source Terms Playbook

## Public Domain Is Not the Same as Publicly Available

Public-domain material may be reusable, but provenance, attribution, access date, and fair-access notes still matter. Publicly available web pages may remain copyrighted or restricted by terms.

## Source Checks

For every source, record:

- source URL or local path;
- source owner;
- source type;
- rights tier;
- license or terms summary;
- robots/site terms status;
- paywall/login status;
- allowed storage and commit posture;
- training/evaluation use limits;
- provenance hash and reviewer/operator.

## SEC EDGAR and Companyfacts

Use official SEC endpoints and fair-access guidance. Default storage is metadata-only. Avoid high-rate polling, hidden scraping, or bulk downloads. Filing facts and references can support event metadata, but transcript bodies from exhibits still require source-specific rights review.

## Company IR

Official IR sources are preferred for transcript-first work when terms allow use. Check the specific company page, linked terms, robots posture, paywall/login status, and whether the transcript body can be stored or only referenced.

## FRED and Macro Data

FRED is useful for macro context, but individual series can have separate source-owner terms. Check series-level source notes before storing or redistributing values.

## External Datasets

External datasets are benchmark/support resources unless explicitly reviewed. They cannot become Signal Engine gold labels. Dataset performance does not prove earnings-call transcript quality.

## Restricted Sources

Restricted transcript-provider bodies, audio, and video stay blocked. Metadata-only references may document the blocked case, but raw bodies must not be copied, committed, trained on, or used for evaluation claims unless explicit license terms allow it.
