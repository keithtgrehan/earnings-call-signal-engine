# App

This folder contains two local review interfaces for the earnings-call pipeline, both backed by the same deterministic workflow.

## Run

```bash
PYTHONPATH=src python app/server.py
```

Open `http://127.0.0.1:7860`.

Backup interface:
- `app/server.py`
- original panel-heavy layout

Primary shell:

```bash
PYTHONPATH=src python app/site_server.py
```

Open `http://127.0.0.1:7861`.

The primary shell now supports two modes in one place:
- `Demo mode`: instant fixed-case loading for Netflix Q1 2022, Meta Q3 2022, and NVIDIA Q4 FY24 using the frozen fixture contracts under `data/demo_cases/`
- `Input mode`: the normal live workflow for YouTube, local media, transcript upload, and pasted transcript text

The primary shell makes the side-by-side raw source vs extracted signal view the main demo surface. The backup interface remains available as a fallback while the shell evolves.

Direct demo URLs:
- `/?mode=demo&demo_case=netflix_q1_2022`
- `/?mode=demo&demo_case=meta_q3_2022`
- `/?mode=demo&demo_case=nvidia_q4_fy2024`

Refresh source note:
- fixed-case source files can be refreshed from `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE`
- copy only the intended case artifacts into the existing `data/demo_cases/<case_id>/` structure; do not dump raw extra files into the repo

Runs execute as local background jobs. The review page refreshes while a run is active, so long YouTube transcriptions do not hold the browser request open.

## Inputs
- YouTube URL
- Local audio/video upload
- Local document upload: `.doc`, `.docx`, `.txt`, `.md`, `.csv`, `.json`
- Pasted transcript text

## Modes
- `Deterministic only`: transcript, sentiment, guidance, guidance revision, tone changes, metrics, report
- `Deterministic + LLM`: keeps deterministic artifacts as source of truth and adds `llm_summary.json`

## Notes
- Document mode uses extracted text and synthetic relative timing. It writes `document_timing_note.txt` to make that explicit.
- Legacy `.doc` extraction tries `textutil`, then `antiword`, then `soffice` if available.
- Demo mode keeps audio bounded to the curated joined-review moments already prepared for the fixed cases.
- Market context stays visible as a secondary sanity-check panel and is not presented as predictive validation.

## Suggested starting prompt

```text
You are reviewing one earnings call. Stay grounded in the deterministic artifacts only. Identify the clearest guidance changes, the strongest tone-change moments, the evidence snippets that support them, and any places where the evidence is still ambiguous. Prefer conservative language over confident speculation. Do not make live trading claims or claim predictive edge.
```
