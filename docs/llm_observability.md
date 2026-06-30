# LLM Observability

Status: scaffolded and disabled by default.

Opik is represented only as optional configuration and a local config validator. It is not called by tests, normal CI, or safe Make targets.

Use `configs/opik.example.yml` to record the intended environment variable names:

- `OPIK_API_KEY`
- `OPIK_WORKSPACE`

Validate without network calls:

```bash
python scripts/check_opik_config.py --path configs/opik.example.yml
```

Do not enable Opik until real provider calls exist and the artifact policy has been checked. Observability payloads must not include API keys, raw restricted transcript bodies, canonical gold labels, or model outputs represented as truth.
