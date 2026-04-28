# NLP Tools And Research Map

This map tracks possible tools and datasets for evaluation readiness. It is not a claim that these tools are implemented, validated, downloaded, or production-ready.

## 1. What Is Implemented Now

- Transcript-first deterministic extraction.
- Standard-library validators for corpus, labels, model registry, training-set registry, and NLP tools registry.
- Deterministic weak-label keyword baseline.
- Metadata-only SEC 8-K intake scaffold.
- Manual first-3 corpus case workflow.

## 2. What Is Scaffolded Only

- Model registry entries.
- Training/evaluation dataset registry entries.
- NLP tools registry entries.
- Optional local sklearn smoke-training scaffold.
- Handcrafted fixtures and weak labels.

These are not real validated training data and not real ML.

## 3. Finance NLP Landscape

Finance candidates include Financial PhraseBank, FinBERT, FLAME, Open FinLLM references, SEC EDGAR metadata, and FINOS earnings-call transcript references. They are useful for future benchmark context, but none are downloaded or validated here.

## 4. Sales NLP Landscape

Sales candidates include HubSpot, Salesforce, Gong, Chorus, objection detection, and next-step/next-best-action taxonomies. These require user-owned exports and manual privacy review before evaluation.

## 5. Support NLP Landscape

Support candidates include Intercom, Zendesk, Freshdesk, escalation labels, and customer support tone labels. These remain candidate sources only until user-owned exports and reviewed labels exist.

## 6. Account-Management NLP

Account-management candidates include Gainsight account-health exports, churn risk labels, renewal risk concepts, and commitment tracking. These are not implemented as production scoring beyond deterministic demo scaffolds.

## 7. Emotion Datasets

Emotion candidates include GoEmotions, DAIR.AI references, DailyDialog, MELD, EmotionLines, EmpatheticDialogues, and support tone labels. These are benchmark references only and do not prove emotion detection in real business conversations.

## 8. Embeddings And Rerankers

Embedding candidates include OpenAI, Voyage, Cohere, Jina, Gemini, Qwen, BGE, and Nomic. Reranker candidates include Cohere, Jina, BGE, and Qwen. They are not part of canonical scoring and should wait until deterministic labels and error analysis are stable.

## 9. Long-Context Models

Long-context candidates include OpenAI, Anthropic, Google, and local Ollama experiments. They are future review aids only, not canonical truth or validated product behavior.

## 10. Why This Is Not Product Proof

- Registries are tracking surfaces only.
- No datasets, model weights, transcripts, audio, video, or API outputs are shipped by this layer.
- No production ML exists here.
- No statistical significance, retrieval quality, market correlation, or long-context benchmark is claimed.
- Deterministic extraction remains the core system.

## 11. Evaluation Roadmap

1. deterministic extraction
2. first 3 manual calls
3. 30-call benchmark
4. error analysis
5. sales/support synthetic comparison
6. user-owned CRM data
7. embeddings/rerankers
8. long-context
9. optional ML
