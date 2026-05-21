# Chunking and Retrieval Object Strategy

Retrieval supports review and benchmarking. It does not override deterministic extraction.

## Object Types

- `evidence_object`: highest-signal object, tied to deterministic extraction or reviewed evidence.
- `event_aligned_chunk`: transcript chunk aligned to a call event, Q&A turn, guidance span, or media event window.
- `semantic_chunk`: generic transcript chunk for recall-oriented retrieval.

## Required Fields

Retrieval objects require object ID, object type, case ID, company, fiscal period, source type/ref, section, speaker, topic, span hints, evidence text or redacted preview, provenance path/span IDs, rights tier, and raw-text commit flag.

## Guardrails

- Missing provenance fails validation.
- Evidence objects should rank above generic chunks.
- Rights fields travel with every retrieval object.
- Retrieval outputs are reviewer support only.
