# Retrieval Fallback Diagnostics

- Retrieval objects: 512
- Object type counts: `{"event_aligned_chunk": 44, "evidence_object": 44, "semantic_chunk": 424}`
- Evidence-ready cases: 29
- Semantic-only cases: 2
- Fallback overuse: 0.093
- evaluated_rag=false
- Raw text returned: false
- Mitigation: `case_prefilter_evidence_required_queries_exclude_semantic_fallback_when_nonsemantic_evidence_exists`

## Semantic-Only Cases

- `lyb_2025_q4`
- `rddt_2025_q2`
