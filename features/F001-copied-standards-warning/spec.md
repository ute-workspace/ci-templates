Status: in-progress
Branch: feature/UND-56-copied-standards-warning
Repositories: ci-templates

# F001 — Copied standards warning

## Goal

Warn consumers when their project contains copied agent standards so they can clean them before enforcement is introduced.

## Scope

- [NEW] `scripts/check-copied-standards.sh` — canonical warning-only check of a project directory; reads nothing from agent-standards.
- [MODIFY] `.github/workflows/{node-ci,container-release,node-container-release,ansible-deploy,gitops-image-promotion}.yml` — embed the check, run against the caller checkout in each reusable workflow.
- [NEW] `tests/test_copied_standards.py` — behavior and workflow integration tests.
- [MODIFY] `.github/workflows/validate.yml` — run the tests.
- [MODIFY] `docs/architecture.md` and `docs/ci-cd.md` — behavior, checkout boundary, validation.

## Acceptance criteria

- AC1: Each reusable workflow checks the caller repository, including deployment workflows that separately check out external repositories.
  Verify: run `python3 -m unittest discover -s tests -v` → `WorkflowIntegrationTest` passes for all five workflows (caller checkout precedes the check, no `repository`/`ref`/`token`, deployment checkouts not inspected).
- AC2: `.agents/core/`, `.agent-standards.yml`, and every entry under `.claude/skills/` and `.agents/skills/` are each reported by path, without reading agent-standards (no list, token, pin, or checkout).
  Verify: run `python3 -m unittest discover -s tests -v` → clean, individual, multiple, and both-skill-directory cases pass.
- AC3: Findings link to upstream `scripts/clean-project.py`, emit warning annotations and a job summary, and do not fail the job.
  Verify: run `python3 -m unittest discover -s tests -v` → findings exit 0 with expected annotations, summary, and link.
- AC4: A missing caller checkout is reported as a visible warning, not as clean.
  Verify: run `python3 -m unittest discover -s tests -v` → missing-checkout case passes.
- AC5: Repository CI runs tests and YAML parsing remains valid.
  Verify: run the local gates in `docs/ci-cd.md` → both pass.

## Deferred

- Failing enforcement after repositories are cleaned, as a separate change.

## Out of scope

- Cleaning consumer repositories or changing Jenkins pipelines.

## Risks

- GitHub Actions has no Jenkins UNSTABLE result; a successful job with warning annotations and a job summary is the accepted equivalent (UND-24 plan).
- Deployment workflows use external checkouts; the caller project is checked out separately to `caller-project` and only that path is inspected.

## Open questions

None.

## Decisions

- Detection uses only fixed paths in the caller project; no upstream source is fetched (UND-24 plan supersedes the earlier pinned-upstream draft).
- The check body is embedded in each workflow rather than fetched from this repository at run time, so no extra checkout, ref, or token is needed; a test keeps every copy identical to `scripts/check-copied-standards.sh`.
