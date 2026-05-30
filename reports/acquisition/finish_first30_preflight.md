# Finish First30 Preflight

- Baseline source: merged PR #56 on `main`.
- First30 target rows: 30 plus HD control fixture.
- Download-allowed rows before this branch: 9.
- Registered transcript rows before this branch: 8 including HD control.
- Parsed transcript rows before this branch: 7.
- Registered audio rows before this branch: 1 VZ prepared MP3.
- ASR complete rows before this branch: 0.
- Audio alignment rows before this branch: 0.
- Normalized transcripts before this branch: 8.
- Chunks/evidence/retrieval objects before this branch: 146 / 8 / 146.
- Retrieval metrics before this branch: recall@1/3/5 0.615 / 0.615 / 0.615, MRR 0.615, citation validity 1.000, wrong case/ticker/period 0, evaluated_rag=false.
- Training readiness before this branch: NOT_READY.

## Replacement State

- Existing replacement rows: 30.
- Existing applied replacement rows: 1 (`jpm_2025_q1`).
- Agent S1 rows not yet applied at preflight: `jpm_2025_q4`, `jpm_2025_q3`, `jpm_2025_q2`, `cat_2025_q3`, `cat_2025_q2`, `cat_2025_q1`, `cat_2024_q4`.
- CAT S1 rows are `s25.q4cdn.com` official IR CDN candidates and require rights review; Q4CDN is not globally trusted.

## Missing First30 Rows

- Missing registered transcripts at preflight: `vz_2024_q4`, `jpm_2025_q4`, `jpm_2025_q3`, `jpm_2025_q2`, `cat_2025_q3`, `cat_2025_q2`, `cat_2025_q1`, `cat_2024_q4`, `crm_2025_q4`, `dow_2025_q4`, `eqt_2025_q4`, `f_2025_q4`, `hig_2025_q4`, `lyb_2025_q4`, `oc_2025_q4`, `omc_2025_q4`, `rddt_2025_q4`, `rf_2025_q4`, `uber_2025_q4`, `vz_2025_q1`, `vz_2025_q2`, `vz_2025_q3`, `vz_2025_q4`.

## Blockers

- VZ full transcript remains vendor-marker blocked; VZ prepared MP3 is support-only.
- CRM Q4CDN transcript remains vendor-marker blocked unless a clean official source or license config is supplied.
- DOW, EQT, F, HIG, LYB, OC, OMC, RDDT, RF, UBER, and VZ 2025 rows still require clean direct official transcript URLs or configured provider access.
- Local ASR package is available from PR #56, but ASR requires a local/cached faster-whisper model or a permitted Desktop model download.
- Retrieval quality has valid citations and no wrong-case/wrong-period hits, but recall/fallback gates still keep evaluated_rag=false.

## Next 10 Source Actions

1. Apply Agent S1 JPM Q4/Q3/Q2 direct PDF replacements.
2. Reconfirm JPM Q1 remains clean and already registered.
3. Apply Agent S1 CAT Q3/Q2/Q1/2024Q4 Q4CDN rows as review-required official IR CDN candidates if clean.
4. Download/parse newly allowed JPM rows into Desktop-only folders.
5. Download/parse newly allowed CAT rows into Desktop-only folders if vendor scan remains clean.
6. Preserve S2 audio gap findings without downloading player-only media.
7. Audit provider key/license readiness without pulling provider raw data.
8. Attempt local faster-whisper tiny model setup into the Desktop model cache.
9. Run VZ prepared-audio ASR only if local model execution is available.
10. Rebuild normalization, chunks, evidence, retrieval, training readiness, and dashboard from registered transcripts only.
