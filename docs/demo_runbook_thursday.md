# Thursday Demo Runbook

## Launch

Preferred:

```bash
./scripts/run_demo_ui.sh
```

Direct fallback:

```bash
PYTHONPATH=src PORT=7872 python3 app/site_server.py
```

URL:

```text
http://127.0.0.1:7872
```

## Demo Order

1. Meta Q3 2022
2. Netflix Q1 2022
3. NVIDIA Q4 FY24

## Click Path

1. Open the URL.
2. Stay in `Demo mode`.
3. Start with `Meta Q3 2022`.
4. Use the `Raw source vs extracted signal` view first.
5. Switch to `Netflix Q1 2022`, then `NVIDIA Q4 FY24`.

## Fallback Order

1. Netflix Q1 2022
2. NVIDIA Q4 FY24
3. Meta Q3 2022

## Quick Troubleshooting

- Server does not start:
  Run the direct fallback command above from the repo root and confirm `python3` is available.
- Page does not load:
  Confirm the terminal shows `Running on http://127.0.0.1:7872` and then refresh the browser.
- A demo case does not appear:
  Go back to `Demo mode` on the landing page and reselect the case from the dropdown.

## Stop / Restart

Stop:

```bash
Ctrl-C
```

Restart:

```bash
./scripts/run_demo_ui.sh
```
