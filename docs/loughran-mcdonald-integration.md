# Loughran-McDonald Integration

This repo treats Loughran-McDonald as canonical lexical support when a local, license-reviewed dictionary export is available.
The raw external CSV is never required for CI, and the baseline still works without it.

- status: `blocked_missing_source`
- expected_input_dir: `data/external/loughran_mcdonald`
- canonical_usage: `optional deterministic lexical support`

## Blocked Status

- No local Loughran-McDonald CSV was found under the expected external data path.
- This is not a runtime failure for the repo. Deterministic rules continue to work without the finance dictionary.

## Manual Steps

1. Place an official Loughran-McDonald master dictionary CSV in `data/external/loughran_mcdonald/`.
2. Run `python scripts/import_loughran_mcdonald.py`.
3. Review the generated normalized artifact before committing it.
