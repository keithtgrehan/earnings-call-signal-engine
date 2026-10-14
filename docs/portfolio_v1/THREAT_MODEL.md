# Portfolio Product V1 Threat Model

Status: initial design threat model; implementation controls are planned unless
marked otherwise.

## Protected Assets

- User identities, roles, and session tokens.
- Uploaded documents and generated evidence bundles.
- Human review decisions and audit history.
- Provider credentials and cloud deployment permissions.
- Evaluation holdout data and unpublished results.
- Cost controls and operational telemetry.
- The integrity of deterministic, model, and human output states.

## Threats and Required Controls

| Threat | Required v1 control | Verification |
|---|---|---|
| Unauthorised document access | Cognito JWTs, owner/role checks on every object/job route, private S3 | Cross-user permission tests |
| Predictable artifact IDs | Non-sequential identifiers plus server-side authorisation | Negative API tests |
| Malicious or oversized upload | Text-only allowlist, strict byte/page limits, content validation, quarantine/fail closed | Upload abuse tests |
| Prompt injection in source text | Models receive a fixed data envelope and system policy; source text cannot issue tool actions | Adversarial evaluation cases |
| Model output treated as truth | Separate immutable deterministic, model, and human records | Schema and state-transition tests |
| Secret disclosure | Secrets Manager, short-lived CI identity, log redaction, secret scanning | CI scan and log review |
| Excessive model/cloud spend | Per-user/run limits, Lambda concurrency cap, token limits, Budgets alerts and kill switch | Budget/limit test |
| Sensitive data retained too long | Documented TTL, delete workflow, S3 lifecycle, no raw uploads in Git | Retention/deletion test |
| Audit tampering or missing lineage | Request/job IDs, append-oriented audit events, hashes and timestamps | End-to-end trace check |
| Dependency/supply-chain compromise | Lock dependencies, GitHub dependency review/CodeQL, pinned CI actions | CI evidence |
| Denial of service | API throttling, queue limits, bounded retries, dead-letter queue | Load/queue failure test |
| Unsupported public claims | Locked evaluation contract and human publication review | Release checklist |

## Privacy and Data Handling

- V1 accepts approved text documents only.
- Store the minimum required source material for the shortest documented period.
- Display and log metadata rather than raw text whenever possible.
- Do not log credentials, complete documents, session tokens, or unnecessary PII.
- PII detection/redaction is a support control, not proof that a document is safe.
- Demo accounts use non-confidential, rights-reviewed material.

## Human Review Boundaries

Human approval is required for gold promotion and published conclusions. The UI
must show source evidence, model identity, uncertainty/disagreement, and whether
text was edited before approval.

## Residual Risk

This remains a portfolio-grade, invite-only demonstration. It will not claim
enterprise multi-tenancy, regulated-data certification, penetration-test
coverage, or production SLA. These limits must remain visible in the case study.

## Review Inputs

Before release, compare this model against the current NIST Generative AI
Profile, OWASP guidance for LLM applications, and the AWS Well-Architected
security and generative-AI guidance. Record material changes in `DECISIONS.md`.
