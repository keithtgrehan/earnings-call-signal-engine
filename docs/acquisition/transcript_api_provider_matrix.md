# Transcript API Provider Matrix

This scaffold tracks paid transcript APIs as metadata-only discovery sources.
Providers stay disabled until API terms, storage rights, evaluation rights, and license references are recorded.

| Provider | Default status | Raw storage | Evaluation use | Training use | Requirement before future raw access |
| --- | --- | --- | --- | --- | --- |
| example_paid_transcript_api | disabled | false | false | false | `license_config_ref` and explicit approval |

Guardrails:

- Disabled providers write skipped reports and exit successfully.
- Missing API keys write skipped reports and exit successfully.
- Missing `license_config_ref` blocks future raw access.
- This layer does not download, store, or commit raw transcripts.
