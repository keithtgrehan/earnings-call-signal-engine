# Portfolio Product V1 Product Spec

Status: accepted product boundary; implementation planned.

## Customer

Primary user: a corporate-strategy, competitive-intelligence, finance, or
investor-relations analyst who reviews permitted earnings materials and needs a
fast, evidence-backed first pass.

Reviewer: a finance or research lead who must approve material conclusions and
retain an audit trail.

This case study is not for automated trading or retail investment advice.

## Problem

Earnings materials are lengthy, repetitive, and difficult to compare reliably.
Generic AI summaries can omit evidence, flatten uncertainty, and make model
quality or cost difficult to assess. Review teams need candidate signals tied to
source evidence, explicit disagreement, and human approval.

## V1 Workflow

1. An authenticated analyst selects an approved demo case or uploads a permitted
   text document.
2. The service validates type, size, source metadata, and retention settings.
3. The existing deterministic engine generates signal candidates and evidence
   spans.
4. Two provider models review the same immutable evidence bundle against one
   output schema.
5. The UI shows deterministic output, model agreement/disagreement, evidence,
   uncertainty, latency, and estimated cost.
6. A reviewer approves, edits, rejects, or abstains and records a reason.
7. The system stores an auditable reviewed result and produces a bounded report.

## Roles

- Analyst: submit permitted documents, run analyses, view own authorised jobs.
- Reviewer: perform analyst actions and decide review outcomes.
- Admin: manage demo users, retention, and operational settings; cannot silently
  promote model output to gold data.

V1 is one controlled demo tenant. Full multi-tenant SaaS isolation is not in
scope, but authorisation checks must be designed so tenant scoping can be added.

## Customer Acceptance Criteria

- A new invited user can sign in without shared credentials.
- The user can complete the happy path without terminal access.
- Every displayed signal links to supporting source evidence.
- Model output is visually distinct from deterministic and human-reviewed state.
- A reviewer can approve, edit, reject, or abstain with a recorded reason.
- Job restarts do not lose job or review state.
- Unauthorised users cannot retrieve another user's documents or artifacts.
- A completed run reports latency, model tokens/cost, infrastructure estimate,
  and human review time.
- The user can request deletion according to the documented retention policy.

## Non-Goals

- Trading, forecasting, portfolio allocation, or alpha claims.
- Audio/video ingest in the deployed v1.
- Open-ended web browsing or agentic research.
- Fine-tuning or automated gold-label promotion.
- Vector database, knowledge graph, Kubernetes, or multi-cloud deployment.
- Scraping paywalled or rights-unclear transcript sources.
- Production-scale SLA, enterprise multi-tenancy, or regulated-customer claims.

## Success Evidence

The case study will report observed results only on its locked, human-reviewed,
non-production evaluation. Business value is framed as analyst-review support,
not replacement of professional judgment.
