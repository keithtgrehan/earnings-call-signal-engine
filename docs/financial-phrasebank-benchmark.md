# Financial PhraseBank Benchmark Adapter

Financial PhraseBank is treated as a benchmark-only sanity-check resource in this repo.
It is not canonical training data and is never mixed into the local support/sales/account-management corpus automatically.

- status: `blocked_missing_source`
- expected_input_dir: `data/external/financial_phrasebank`
- default_path: `benchmark_only`

## Blocked Status

- No local PhraseBank files were found under `data/external/financial_phrasebank/`.
- CI and benchmark scripts should continue without it.

## Manual Steps

1. Place a locally licensed PhraseBank export in `data/external/financial_phrasebank/`.
2. Run `python scripts/import_financial_phrasebank.py`.
3. Use the normalized output only for benchmark-only sanity checks.
