# Ilya Reading List Research Intelligence Layer

This folder distills a public mirror of Ilya Sutskever's widely circulated AI reading list into reusable Signal Engine 2.0 project assets. It is a research and planning layer, not a claim that these papers have been implemented as production models.

## What Is Included

- Paper-level summaries with authors, years, technical concepts, Signal Engine relevance, risks, and implementation status.
- A machine-readable metadata set under `data/research/ilya_reading_list/`.
- A research-to-feature matrix connecting papers to transcript NLP, RAG, evaluation, multimodal intelligence, scaling, and future AI tooling.
- A lightweight CLI at `tools/research_paper_map.py`.
- A local keyword search scaffold under `src/signal_engine/research/`.

## Current Status

All papers are marked `research_only`. The repo now has metadata, documentation, and lookup utilities. It does not train neural networks, add external APIs, require vector databases, or replace deterministic Signal Engine behavior.

## Quick Commands

```bash
python tools/research_paper_map.py --list
python tools/research_paper_map.py --paper attention_is_all_you_need
python tools/research_paper_map.py --category attention_transformers
python tools/research_paper_map.py --signal-engine-roadmap
python tools/research_paper_map.py --export-markdown
```

## Reading Order

Use `data/research/ilya_reading_list/learning_paths.json` for curated paths. The most practical route for this repo is the Signal Engine 2.0 Practical Roadmap path: MDL/evaluation, attention, pointer evidence, scaling laws, ASR, and graph/message-passing ideas.
