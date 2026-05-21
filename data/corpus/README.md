# Corpus Data Guardrails

`data/corpus/` is for corpus manifests, metadata, provenance records, and local case scaffolds.

Do not commit raw restricted transcript bodies, provider text, audio, video, generated review packets, or bulky processed artifacts unless a resource registry record explicitly allows raw-body commit and preserves provenance. Publicly reachable pages are not automatically open licensed.

Use `configs/resource_registry.example.yml` and `scripts/validate_resource_registry.py` before adding new source classes. Weak-label outputs remain review candidates only.
