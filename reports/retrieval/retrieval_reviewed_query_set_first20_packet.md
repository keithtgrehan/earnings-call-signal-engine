# First20 Reviewed Retrieval Query-Set Packet

Status: `review_pending`

This packet supports manual review of `data/retrieval/retrieval_reviewed_query_set.first20.jsonl`. It is metadata-only and does not contain source content.

## Run Boundary

- Query rows: `20`
- Review status: `review_pending`
- Benchmark-eligible rows: `0`
- Provider execution: `disabled`
- Embeddings generated: `false`
- Vector DB generated: `false`
- Evaluated retrieval quality: `false`
- Production RAG claim: `false`

## Review Instructions

Reviewers should inspect the local source span outside git using `provenance_ref` plus `span_start_char` and `span_end_char` from `data/retrieval/retrieval_object_metadata.jsonl`.

Do not paste raw transcript text, chunk text, evidence text, ASR/audio text, answer text, provider responses, embeddings, vectors, labels, adjudication data, training data, or promotion rows into the JSONL or this packet.

Rows may become eligible only after a reviewer confirms the row links to the intended case, object type, topic, section, speaker role, source hash, text hash, provenance hash, provenance ref, and span offsets.

## Candidate Rows

| query_id | query_type | case_id | object_id | object_type | topic | section | speaker | provenance_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rq_first20_bac_2025_q4_001 | evidence_object_lookup | bac_2025_q4 | rom_evidence_652ec646a4acb874 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/BAC_Bank_of_America_Corporation/bac_2025_q4/metadata/normalized_transcript.json |
| rq_first20_cat_2025_q4_002 | evidence_object_lookup | cat_2025_q4 | rom_evidence_68b3fd2836e8f79a | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/CAT_Caterpillar_Inc/cat_2025_q4/metadata/normalized_transcript.json |
| rq_first20_f_2025_q1_003 | topic_lookup | f_2025_q1 | rom_evidence_40d152c6689eaf6d | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/F_Ford_Motor_Company/f_2025_q1/metadata/normalized_transcript.json |
| rq_first20_f_2025_q2_004 | case_comparison_lookup | f_2025_q2 | rom_evidence_8478c18d3901ee2d | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/F_Ford_Motor_Company/f_2025_q2/metadata/normalized_transcript.json |
| rq_first20_f_2025_q3_005 | case_comparison_lookup | f_2025_q3 | rom_evidence_22a43d167f7aed1a | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/F_Ford_Motor_Company/f_2025_q3/metadata/normalized_transcript.json |
| rq_first20_f_2025_q4_006 | case_comparison_lookup | f_2025_q4 | rom_evidence_00c74f1cee2427dc | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/F_Ford_Motor_Company/f_2025_q4/metadata/normalized_transcript.json |
| rq_first20_hd_2024_q1_007 | topic_lookup | hd_2024_q1 | rom_evidence_5b19f6a7ce0cc6d7 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/HD_The_Home_Depot_Inc/hd_2024_q1/metadata/normalized_transcript.json |
| rq_first20_hd_2024_q2_008 | case_comparison_lookup | hd_2024_q2 | rom_evidence_b97a0f25e958c20f | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/HD_The_Home_Depot_Inc/hd_2024_q2/metadata/normalized_transcript.json |
| rq_first20_hd_2024_q3_009 | case_comparison_lookup | hd_2024_q3 | rom_evidence_f151ef7ee8e00af8 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/HD_The_Home_Depot_Inc/hd_2024_q3/metadata/normalized_transcript.json |
| rq_first20_hd_2024_q4_010 | case_comparison_lookup | hd_2024_q4 | rom_evidence_2f49870771e37ca4 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/HD_The_Home_Depot_Inc/hd_2024_q4/metadata/normalized_transcript.json |
| rq_first20_hd_2025_q4_011 | evidence_object_lookup | hd_2025_q4 | rom_evidence_1c3e749b1346dbbc | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/HD_The_Home_Depot_Inc/hd_2025_q4/metadata/normalized_transcript.json |
| rq_first20_jpm_2024_q1_012 | uncertainty_language_lookup | jpm_2024_q1 | rom_evidence_03b94f2d82a4423a | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/JPM_JPMorgan_Chase_Co/jpm_2024_q1/metadata/normalized_transcript.json |
| rq_first20_jpm_2024_q1_guidance_013 | guidance_revision_lookup | jpm_2024_q1 | rom_evidence_82b7153a53608d62 | evidence_object_metadata | guidance_statement | guidance_statement | mixed | /Users/keith/Desktop/earnings calls 100 samples/JPM_JPMorgan_Chase_Co/jpm_2024_q1/metadata/normalized_transcript.json |
| rq_first20_jpm_2024_q2_014 | case_comparison_lookup | jpm_2024_q2 | rom_evidence_c04c6c85d0287e43 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/JPM_JPMorgan_Chase_Co/jpm_2024_q2/metadata/normalized_transcript.json |
| rq_first20_jpm_2024_q3_015 | case_comparison_lookup | jpm_2024_q3 | rom_evidence_96da72f32f422fc6 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/JPM_JPMorgan_Chase_Co/jpm_2024_q3/metadata/normalized_transcript.json |
| rq_first20_jpm_2024_q4_016 | case_comparison_lookup | jpm_2024_q4 | rom_evidence_d50d61dc3c6939a9 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/JPM_JPMorgan_Chase_Co/jpm_2024_q4/metadata/normalized_transcript.json |
| rq_first20_lyb_2025_q1_017 | analyst_pressure_lookup | lyb_2025_q1 | rom_evidence_406031ab57d43c59 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/LYB_LyondellBasell_Industries_N_V/lyb_2025_q1/metadata/normalized_transcript.json |
| rq_first20_lyb_2025_q2_018 | case_comparison_lookup | lyb_2025_q2 | rom_evidence_805c6e0027371a06 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/LYB_LyondellBasell_Industries_N_V/lyb_2025_q2/metadata/normalized_transcript.json |
| rq_first20_uber_2025_q4_guidance_019 | guidance_revision_lookup | uber_2025_q4 | rom_evidence_93fae8ca92fee2dd | evidence_object_metadata | guidance_revision_candidate | guidance_revision_candidate | mixed | /Users/keith/Desktop/earnings calls 100 samples/UBER_Uber_Technologies_Inc/uber_2025_q4/metadata/normalized_transcript.json |
| rq_first20_rddt_2025_q4_020 | evidence_object_lookup | rddt_2025_q4 | rom_evidence_c89fd74de4561528 | evidence_object_metadata | prepared_remarks | prepared_remarks | management | /Users/keith/Desktop/earnings calls 100 samples/RDDT_Reddit_Inc/rddt_2025_q4/metadata/normalized_transcript.json |

## Reviewer Decision Checklist

For each row, confirm:

- `object_id` exists in `data/retrieval/retrieval_object_metadata.jsonl`.
- `case_id`, `ticker`, and fiscal period match the intended row.
- `object_type`, topic, section label, and speaker role match the row intent.
- Source hash, text hash, normalized transcript hash, and provenance hash are present in metadata.
- `provenance_ref` and span offsets point to the intended local span.
- The safe query label is not copied source content.
- The row remains `benchmark_eligible=false` until review is complete.

## Current Blockers

- Manual review has not been completed.
- `reviewer` and `reviewed_at` are intentionally empty.
- `benchmark_eligible=false` for all rows.
- Provider execution remains disabled.
- This packet does not report retrieval quality or provider performance.
