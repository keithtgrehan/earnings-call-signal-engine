# Gold Labeling Review Packet

Use these packet files to choose human-reviewed gold labels. Weak labels are suggestions only.

| case_id | packet | selected 5 labels | confirmed exact quotes | confirmed final labels | saved JSONL | validated |
| --- | --- | --- | --- | --- | --- | --- |
| AAPL_2026_Q1 | `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/AAPL_2026_Q1/labels/human_labeling_packet.md` | [ ] | [ ] | [ ] | [ ] | [ ] |
| AMZN_2025_Q4 | `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/AMZN_2025_Q4/labels/human_labeling_packet.md` | [ ] | [ ] | [ ] | [ ] | [ ] |
| META_2025_Q4 | `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/META_2025_Q4/labels/human_labeling_packet.md` | [ ] | [ ] | [ ] | [ ] | [ ] |
| MSFT_2026_Q1 | `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/MSFT_2026_Q1/labels/human_labeling_packet.md` | [ ] | [ ] | [ ] | [ ] | [ ] |
| NVDA_2026_Q4 | `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/NVDA_2026_Q4/labels/human_labeling_packet.md` | [ ] | [ ] | [ ] | [ ] | [ ] |

After editing `gold_labels.jsonl`, run:

```bash
python tools/transcript_downloader/validate_gold_labels.py --root "/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts"
```
