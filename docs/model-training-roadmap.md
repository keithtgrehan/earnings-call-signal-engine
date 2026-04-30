# Model Training Roadmap

This roadmap keeps deterministic extraction as the baseline and human-reviewed evidence spans as the benchmark source of truth.

## Phase 1: Label Workflow Hardening

- Audit selected-candidate CSVs before conversion.
- Keep draft labels separate from human-approved gold labels.
- Maintain the 31-case earnings-call corpus.
- Target 5-15 human-reviewed labels per case first.
- Expand each labeled case toward 15-25 labels.
- Run conservative error analysis without precision/recall/F1 claims until the benchmark is mature enough.

## Phase 2: Financial Baselines

- Financial PhraseBank sanity-check baseline after manual licensed export.
- Loughran-McDonald lexicon baseline after official local CSV is supplied.
- FinBERT comparison for sentence-level finance sentiment.
- Simple logistic regression or sklearn baseline over deterministic features.
- Transformer baseline only as a comparison layer, not proof of transcript reasoning.

## Phase 3: Multi-Domain Schemas

- Sales: objections, buyer intent, budget pressure, next steps.
- Support: frustration, escalation, severity, resolution.
- Renewals: churn risk, blockers, value realization, expansion.
- HR: engagement risk, policy concern, follow-up commitment.
- Synthetic fixtures may be used for smoke tests only and must be clearly marked synthetic.
- Human review packet workflow should be reused for each domain.

## Phase 4: Domain Classifiers And Hybrid Evaluation

- Train and evaluate domain-specific classifiers only after enough human-reviewed labels exist.
- Compare deterministic, ML, and hybrid systems against the same gold labels.
- Build explainability reports with evidence spans.
- Reject ungrounded outputs.
- Keep draft and final labels separate in every report.

## What This Roadmap Does Not Claim

- No statistical significance until the label count and sampling plan support it.
- No production ML performance claim from fixture-only tests.
- No alpha, trading edge, stock prediction, or investment advice.
