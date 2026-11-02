# F001 — Copied standards warning

Status: draft
Branch: feature/UND-24-copied-standards-warning
Repositories: ci-templates

## Goal

Warn consumers when their project contains copied agent standards so they can clean them before enforcement is introduced.

## Scope

- [EXISTS] `ute-workspace/agent-standards` commit `6d313db2e1099aa0d064e8558781b15259e61ad1` — source of current, vendor, and retired skill names.
- [MODIFY] `.github/workflows/{node-ci,container-release,node-container-release,ansible-deploy,gitops-image-promotion}.yml` — run the shared check against the caller checkout in each reusable workflow.
- [MODIFY] `.github/workflows/validate.yml` — run the new automated tests.
- [NEW] Shared check and tests — read the pinned upstream checkout at runtime, identify copied paths, and report warnings.
- [MODIFY] `docs/architecture.md` and `docs/ci-cd.md` — describe behavior, dependency, and validation.

## Acceptance criteria

- AC1: Each reusable workflow checks the caller repository, including deployment workflows that separately check out external repositories.
  Verify: inspect all five workflow files and run the workflow integration tests → each invokes the shared check against a caller checkout.
- AC2: `.agents/core/`, `.agent-standards.yml`, and matching skill directories under `.claude/skills/` or `.agents/skills/` are each reported by path; unrelated skills are ignored. Names come from pinned upstream `skills/`, `vendor-skills/`, and `RETIRED_SKILLS`.
  Verify: run `python3 -m unittest discover -s tests -v` → clean, individual, combined, retired, and unrelated skill cases pass.
- AC3: Findings provide a link to upstream `scripts/clean-project.py` and do not fail the build; a visible GitHub Actions warning communicates the condition.
  Verify: run `python3 -m unittest discover -s tests -v` → findings yield successful warning-mode execution and expected annotation and link.
- AC4: Missing or unreadable upstream source is visibly reported and does not masquerade as a clean check.
  Verify: run `python3 -m unittest discover -s tests -v` → source-error case produces a visible warning.
- AC5: Repository CI runs tests and YAML parsing remains valid.
  Verify: run the documented local gates in `docs/ci-cd.md` → both pass.

## Deferred

- Failing enforcement after repositories are cleaned, as requested for a separate change.

## Out of scope

- Cleaning consumer repositories or changing Jenkins pipelines.

## Risks

- GitHub Actions has no Jenkins UNSTABLE build result; use a successful job with warning annotations and a summary, subject to review of that platform mapping.
- Fetching upstream adds a network dependency; report source failures visibly without blocking warning-mode pipelines.
- Deployment workflows use protected or external checkouts; isolate caller checkout and do not inspect the deployment repository by mistake.

## Open questions

None.

## Decisions

- Pin the complete upstream commit SHA and derive names from its actual source at runtime, without vendoring a list.
