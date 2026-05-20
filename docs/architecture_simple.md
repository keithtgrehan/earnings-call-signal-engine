# Simple Architecture

```mermaid
flowchart LR
  A["Transcript"] --> B["Deterministic Signal Rules"]
  B --> C["Evidence Spans"]
  C --> D["Human Review Packet"]
  D --> E["Accepted Rows Only"]
  E --> F["Canonical Gold Labels"]
  F --> G["Evaluation Loop"]
  G --> H["Source-Quality Reports"]
  G --> I["ML Benchmark Sidecar"]
  G --> J["Retrieval Benchmark Sidecar"]
  H --> K["Portfolio/Demo Reports"]
  I --> K
  J --> K
```

Deterministic output remains canonical. Human review grows the gold set. ML and retrieval are sidecars for benchmarking and search/review readiness; they do not override labels.

## Gates

- ML benchmark: allowed after `>=50` labels.
- Retrieval benchmark: allowed after `>=100` labels or explicit experiment mode.
- External datasets: local verified files only.
- Gold promotion: accepted human-reviewed rows only.
