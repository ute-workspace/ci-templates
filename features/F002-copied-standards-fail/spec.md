Status: in-progress
Branch: feat/NO-TICKET-copied-standards-fail
Repositories: ci-templates

# F002 — Fail on copied standards

## Goal

Fail the reusable workflows when the caller project contains copied agent standards. Every consumer repository has been cleaned, so the warning-only check from F001 becomes enforcement (agent-standards#42, decision 6).

## Scope

- [MODIFY] `scripts/check-copied-standards.sh` — findings become `::error` annotations and exit 1.
- [MODIFY] `.github/workflows/{node-ci,container-release,node-container-release,ansible-deploy,gitops-image-promotion}.yml` — embed the new body; drop `continue-on-error` from the check step.
- [MODIFY] `tests/test_copied_standards.py` — failing semantics, non-blocking "not checked" cases.
- [MODIFY] `docs/architecture.md`, `docs/ci-cd.md`, `AGENTS.md` — current behaviour.

## Acceptance criteria

- AC1: Any finding (`.agents/core`, `.agent-standards.yml`, an entry under `.claude/skills/` or `.agents/skills/`, a symlinked `.agents`/`.claude`/skills path) prints one `::error` annotation per path, lists it in the job summary with the `clean-project.py` link, and exits 1.
  Verify: run `python3 -m unittest discover -s tests -v` → `CheckBehaviourTest` finding cases and `SparseCheckoutIntegrationTest` pass.
- AC2: The check step in every reusable workflow has no `continue-on-error`, so a finding fails the job before any build, push, deploy or promotion step.
  Verify: `WorkflowIntegrationTest.test_embedded_check_matches_script` and `test_embedded_step_fails_on_findings` pass.
- AC3: A missing caller checkout or a caller checkout whose outcome is not `success` stays a `::warning` "not checked" result with exit 0; an entry that cannot be listed is not a finding.
  Verify: missing/failed-checkout and unreadable-skill-directory cases pass.
- AC4: YAML parsing and the unit tests pass.
  Verify: run the local gates in `docs/ci-cd.md` → both pass.

## Out of scope

- Jenkins pipelines (`jenkins-library`) and cleaning consumer repositories.
