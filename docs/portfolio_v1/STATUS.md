# Portfolio Product V1 Status

Last updated: 2026-10-14

## Milestone

Control-room foundation and repository automation.

## State

- Publication base: canonical `main` at `929aa9e528f8448c6c806ca7a11668c52f7f3f2b`.
- Integration branch: `codex/portfolio-v1-integration`.
- Local setup: built and validated; included in the October 14 main-publication commit at Keith's explicit request.
- Cloud resources: not created.
- Public deployment: not created.
- Current product proof: local deterministic/review/evaluation foundation only.
- Strict model-quality publication: blocked until provenance-complete,
  human-reviewed evaluation data exists.

## Built and Validated

- Existing transcript-first deterministic extraction and evidence workflows.
- Existing human-review, label-promotion, and evaluation gates.
- Fresh clean Portfolio V1 checkout from current `origin/main`.

## Included in the Main Publication

- Durable control-room document set and status source of truth.
- GitHub issue and pull-request contracts.
- Local preflight, fail-closed release check, targeted tests, and pinned-action
  GitHub Actions workflow.

## Next Three Tasks

1. Repair the pre-existing canonical training-readiness CLI/test mismatch and
   restore a green repository-wide test/lint baseline in a separate focused task.
2. Reconcile the provenance status of evaluation candidates and define the first
   rights-cleared calibration and holdout batches.
3. Produce the AWS infrastructure decision record and minimum deployable CDK
   skeleton without creating cloud resources.

## Blockers Requiring Keith

- AWS account/region, credential method, and initial spend cap before deployment.
- Creating GitHub issues/PRs remains separate work; Keith explicitly authorized this main publication on October 14.
- Approval of any evaluation data whose reuse rights are not already recorded.
- Approval before new cloud deployment or new public evaluation claims. The October 14 instruction authorizes publishing these existing local repository updates to `main`.

## Latest Validation

Publication validation on 2026-10-14:

- `make portfolio-v1-check`: passed after integrating current main; document contract, links, restricted-artifact checks, five tests, syntax and targeted Ruff.
- This publishes the existing planning and validation foundation. It does not deploy the planned cloud product or claim its release checklist is complete.

Historical baseline checks on 2026-08-24 (not rerun or relabelled as current):

- `make portfolio-v1-check`: passed; control-room contract, Markdown links,
  restricted-artifact check over all 22 changed paths, five targeted positive
  and fail-closed tests, syntax, and targeted Ruff.
- `bash -n` for all three Portfolio V1 shell scripts: passed.
- `actionlint .github/workflows/portfolio-v1.yml`: passed.
- `make corpus-safe-check`: passed; generated report changes from the check were
  restored and are not part of the setup diff.
- `python3 -m pytest -q`: baseline is not green — `1000` passed and `1` failed.
  The failing canonical training-readiness CLI test also fails on an untouched
  clean clone of `main`, so it is pre-existing and outside this setup diff.
- `ruff check .`: baseline is not green — `31` pre-existing findings, including
  duplicated imports/CLI definitions in `scripts/report_training_readiness.py`.
  Targeted lint for all new Python files passes.

## Update Rule

This file records validated state, not intended work. A task may update it only
after the control room has reviewed the handoff evidence.
