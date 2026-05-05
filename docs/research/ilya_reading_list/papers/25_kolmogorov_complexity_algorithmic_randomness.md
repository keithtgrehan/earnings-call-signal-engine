# Kolmogorov Complexity and Algorithmic Randomness

## Status

- Source status: citation
- Parse status: citation_only
- Confidence: medium
- Source URL: https://www.ams.org/bookpages/surv-220

## Executive Summary

Kolmogorov Complexity and Algorithmic Randomness is included here as a research asset for Signal
Engine 2.0, not as an implemented model. The core idea is: Algorithmic information theory studies
the shortest descriptions of objects and formal notions of randomness. Historically, It provides the
mathematical background behind MDL, complexity, and randomness discussions on the list. For the
earnings-call project, the practical value is to translate this idea into evidence-first transcript
workflows, safer retrieval, clearer model-selection gates, and explicit limits on what the system
claims. The parsed source status is citation_only; raw source text was processed locally when
available but not committed because redistribution rights differ by publisher and author site. The
useful engineering lesson is to preserve deterministic behavior, add optional research sidecars only
behind evaluation gates, and require source evidence for every signal that might affect an analyst
or portfolio-review narrative.

## Core Technical Idea

Algorithmic information theory studies the shortest descriptions of objects and formal notions of
randomness.

## Key Concepts

- Kolmogorov complexity: research concept relevant to compression_mdl_complexity.
- algorithmic randomness: research concept relevant to compression_mdl_complexity.
- Martin-Lof randomness: research concept relevant to compression_mdl_complexity.
- description length: research concept relevant to compression_mdl_complexity.

## Architecture / Method

Mechanically, this source belongs to `compression_mdl_complexity` and centers on Kolmogorov
complexity, algorithmic randomness, Martin-Lof randomness, description length. In Signal Engine
terms, the method should be treated as a design pattern: identify the data object, preserve
provenance, define the transformation, and test whether it improves evidence quality, not just model
elegance.

Detected source sections: not detected. Parsed text length recorded locally: 0 characters.

## Why It Mattered

It provides the mathematical background behind MDL, complexity, and randomness discussions on the
list.

## What To Learn From It

Random-looking text can be hard to compress but still useless; complexity needs task context.

## Signal Engine 2.0 Relevance

- transcript sectioning: use the paper to decide whether chronology, sections, or context windows matter for a signal.
- speaker-turn modeling: apply the lesson to management/analyst role structure only when labels support it.
- evidence span extraction: prefer citation-first outputs and measure whether the system points to the right text.
- sentiment/emotion/intent scoring: use as a candidate sidecar idea, never as proof of validated sentiment lift.
- weak labeling: convert the research idea into auditable rule checks before using it to generate labels.
- active learning: prioritize uncertain or high-signal-density transcript spans for human review.
- multimodal audio/video roadmap: treat media features as residual evidence over transcripts unless media labels exist.
- RAG/retrieval: evaluate recall, citation precision, and usefulness before adding heavier retrieval infrastructure.
- evaluation: define an ablation and a failure mode before any implementation work starts.

## Direct Feature Ideas

- Boilerplate/compressibility research note
- Randomness-vs-signal caveat in feature docs
- compression_mdl_complexity evaluation note for reviewer-facing Signal Engine workflows
- compression_mdl_complexity evaluation note for reviewer-facing Signal Engine workflows
- compression_mdl_complexity evaluation note for reviewer-facing Signal Engine workflows

## Implementation Backlog

### now

- Add a research note or deterministic diagnostic that can run on existing transcript artifacts.
- Use the idea to improve evidence-span review, weak-label audits, or retrieval evaluation.

### later

- Promote to optional local model or reranker experiments only after stable held-out labels exist.
- Measure lift over deterministic baselines with reviewer-facing error analysis.

### avoid_for_now

- Do not claim neural implementation from this research brief alone.
- Do not replace the deterministic engine with an opaque model before evaluation gates are met.

## Risks / Limitations

- Book-level theory, not an implementation
- Kolmogorov complexity is uncomputable in general

## Practical Takeaway

Keith should remember this paper as a source of design pressure, not a shortcut. The project value
comes from turning the research lesson into small, testable Signal Engine assets: explicit evidence,
clear labels, source-grounded retrieval, and honest claims about what has and has not been
implemented.
