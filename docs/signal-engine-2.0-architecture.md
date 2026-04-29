# Signal Engine 2.0 Architecture

## Canonical Flow

Conversation JSON / transcript  
→ optional PII redaction  
→ schema validation  
→ domain routing  
→ deterministic features  
→ risk/opportunity flags  
→ evidence objects  
→ JSON/report outputs

## Mermaid View

```mermaid
flowchart LR
    A["Conversation JSON / transcript"] --> B["Optional PII redaction"]
    B --> C["Schema validation"]
    C --> D["Domain routing"]
    D --> E["Deterministic features"]
    E --> F["Risk / opportunity flags"]
    E --> G["Evidence objects"]
    F --> H["JSON / report outputs"]
    G --> H

    C -. optional benchmark path .-> I["Transformer text emotion benchmark"]
    A -. optional future .-> J["ASR"]
    J -. optional future .-> K["Diarization"]
    A -. optional future .-> L["Audio features"]
    A -. optional future .-> M["Video / keyframe analysis"]
    C -. optional future .-> N["Retrieval"]
    I -. later fusion .-> O["Multimodal fusion"]
    K -. later fusion .-> O
    L -. later fusion .-> O
    M -. later fusion .-> O
    N -. later fusion .-> O
```

## Notes

- deterministic transcript output remains canonical
- optional emotion, model, audio, and video layers are enrichment or roadmap only
- no truth-detection claim is made anywhere in the architecture
- no black-box emotion score becomes canonical product truth
