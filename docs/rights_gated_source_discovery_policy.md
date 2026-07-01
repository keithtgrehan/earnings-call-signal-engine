# Rights-Gated Source Discovery Policy

Source discovery is metadata-first. It must not be called scraping in code or docs.

Default policy:

- Exchange: `NYSE`
- Lookback: `5 years`
- Raw body ingest default: `false`
- Unknown rights default: `blocked`
- Source terms check required: `true`
- Robots check required: `true`
- Vendor raw ingest requires `license_config_ref`
- YouTube raw media/transcript requires explicit authorization
- SEC/EDGAR discovery is metadata-only unless explicit approval changes the policy

Allowed source types are listed in `configs/source_discovery_policy_5y_nyse.example.yml`.

Official IR raw use is allowed only when terms and robots are reviewed, rights permit storage, and storage/commit/eval flags are explicit.
