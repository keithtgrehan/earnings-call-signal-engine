# Cross-Domain Metrics

Status: evaluation planning document only. These metrics do not imply current model performance, production readiness, statistical significance, or trading utility.

## Finance extraction

- precision
- recall
- macro F1
- direction accuracy

## Evidence quality

- exact span match
- partial span match
- invalid citation rate

## Retrieval

- recall@k
- MRR
- nDCG
- latency
- cost

## Reviewer

- faithfulness
- unsupported claim rate
- citation quality

## Dating safety

- harassment recall
- pressure-language precision
- false-positive rate

## Privacy

- redaction pass rate
- deletion/export success

## Affective

- macro F1
- calibration/ECE
- abstain rate
- reviewer usefulness

## Claim gates

Metrics must be reported with source counts, label provenance, rights status, and evaluation split notes. Do not claim statistical significance without sufficient data and a documented design. Do not report trading, alpha, deception, mental-health, biometric identity, workplace/education emotion, universal emotion truth, or relationship manipulation conclusions.
