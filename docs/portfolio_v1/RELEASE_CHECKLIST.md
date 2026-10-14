# Portfolio Product V1 Release Checklist

This checklist is intentionally fail-closed. Unchecked release gates mean the
case study is not ready for public claims or merge to `main`.

## Repository and Build

- [ ] Final diff is limited to approved Portfolio V1 scope.
- [ ] Existing full test/lint and corpus-safety gates pass.
- [ ] UI production build and browser smoke tests pass.
- [ ] CDK synthesis and policy/security checks pass.
- [ ] CI uses short-lived credentials and contains no committed secrets.
- [ ] Rollback procedure has been rehearsed or dry-run.

## Product Workflow

- [ ] Invited analyst can sign in and submit an approved text case.
- [ ] Job state survives worker/API restart.
- [ ] Evidence and model disagreement are understandable.
- [ ] Reviewer can approve, edit, reject, or abstain.
- [ ] Audit trail captures identity, model/config, evidence hash, and decision.
- [ ] Retention and deletion workflow is tested.

## Evaluation

- [ ] Every headline case has rights status, provenance, hash, and human review.
- [ ] Development and locked holdout splits are versioned and reproducible.
- [ ] Final prompts, schemas, model IDs, parameters, code SHA, and dataset version are frozen.
- [ ] Quality, evidence support, failures, p50/p95 latency, and cost are reported.
- [ ] Cost per successful analysis uses the contract definition.
- [ ] False positives, false negatives, abstentions, and disagreement are shown.
- [ ] Claims are labelled small-sample, human-reviewed, and non-production.
- [ ] No trading, alpha, causality, statistical-significance, or professional-replacement claim is implied.

## Security and Operations

- [ ] Analyst/reviewer/admin authorisation tests pass.
- [ ] Cross-user document/artifact access tests fail closed.
- [ ] Upload type/size and prompt-injection cases are tested.
- [ ] Secrets, PII, and document bodies are absent from logs.
- [ ] CloudWatch dashboard traces one job end to end.
- [ ] Error, dead-letter queue, and budget alerts have been triggered safely.
- [ ] AWS budgets and concurrency/token limits cap accidental spend.

## Public Proof Package

- [ ] Architecture diagram matches deployed reality.
- [ ] Threat model lists implemented and residual controls accurately.
- [ ] Six-minute demo has been rehearsed and recorded.
- [ ] One-page executive business case includes baseline, result, cost, risk, and rollout.
- [ ] Public README clearly separates built, limited, gated, and planned work.
- [ ] No confidential, rights-restricted, credential, or shared-login material is exposed.

## Human Approval

- [ ] Keith approved evaluation wording and business claims.
- [ ] Keith approved public deployment and publication.
- [ ] Keith approved the final PR and merge to `main`.
