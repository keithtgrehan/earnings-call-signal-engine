# Final Priority Review Validation

- current_gold_label_count: `57`
- labels_needed_to_reach_100: `43`
- labels_needed_to_reach_250: `193`
- calls_ready_for_review: `6`
- calls_needing_transcript_download: `1`
- review_packet_rows: `74`
- expected_accepted_labels_if_6_per_ready_call: `36`
- expected_accepted_labels_if_8_per_ready_call: `48`

## Current Metrics

- precision: `0.8399`
- recall: `0.8326`
- F1: `0.8276`

## ML And Retrieval

- ML benchmark: `{'precision': '0.7332', 'recall': '0.7328', 'f1': '0.7327'}`
- retrieval benchmark: `skipped: Retrieval benchmark requires >=100 labels or --enable-retrieval-experiment.`

## Demo Status

- demo_report_exists: `True`

## Review Assets

- review_packet_csv: `data/labeling/priority_review_packet.csv`
- review_packet_markdown: `data/labeling/priority_review_packet.md`
- call_inventory: `reports/call_review_inventory.md`
- transcript_download_plan: `reports/transcript_download_plan.md`
