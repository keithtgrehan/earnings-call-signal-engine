# NLP Assets Registry

This registry tracks datasets, lexicons, model references, benchmark suites, and local NLP tooling for Signal Engine 2.0. It is an audit and preparation layer, not proof that every asset is downloaded, licensed for redistribution, or validated.

Raw data and bulky source artifacts belong in ignored local cache paths under `data/nlp_assets/cache/` or `data/nlp_assets/raw/`. Committed files are manifests, docs, and validation summaries only.

## Category Counts

- `audio_asr_prosody`: 9
- `dialogue`: 8
- `embeddings_retrieval_tools`: 8
- `evaluation_safety`: 7
- `finance`: 9
- `intent`: 2
- `local_nlp_tools`: 4
- `privacy`: 2
- `qa_retrieval`: 7
- `sentiment_emotion`: 6
- `video_multimodal`: 8
- `weak_labeling`: 1

## CLI

```bash
python tools/nlp_asset_map.py --list
python tools/nlp_asset_map.py --category finance
python tools/nlp_asset_map.py --downloaded
python tools/nlp_asset_map.py --manual-required
python tools/nlp_asset_map.py --signal-engine-area weak_labeling
python tools/nlp_asset_map.py --priority high
python tools/nlp_asset_map.py --validate
```
