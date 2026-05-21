# Argilla Setup

Argilla is optional review infrastructure. The deterministic pipeline runs without it.

## Install

Minimal install:

```bash
pip install -e .
```

Review install:

```bash
pip install -e ".[review]"
```

## Environment

The bootstrap script is local-first and reads:

- `ARGILLA_API_URL`, default `http://localhost:6900`
- `ARGILLA_API_KEY`, default `argilla.apikey`
- `ARGILLA_WORKSPACE`, default `signal-engine`
- `ARGILLA_DATASET`, default `earnings-call-review`

Non-local URLs are rejected unless `ARGILLA_ALLOW_REMOTE=true` is set intentionally.

## Bootstrap

Start a local Argilla server using your preferred local setup, then run:

```bash
make review-bootstrap
```

The script validates the connection, creates the workspace if missing, and creates the dataset if missing. It is safe to rerun.

## Dataset Shape

The dataset stores transcript chunk text, provenance metadata, deterministic suggestions, and human multi-label review decisions for:

- `guidance_revision`
- `tone_shift`
- `analyst_pressure`
- `uncertainty`
- `evasive_answer`
- `positive_surprise`
- `negative_surprise`

## Troubleshooting

If `argilla` is missing, install review extras with:

```bash
pip install -e ".[review]"
```

If the server cannot be reached, confirm `ARGILLA_API_URL` points to a running local Argilla instance. Do not commit API keys, Argilla volumes, exports, or reviewer scratch files.
