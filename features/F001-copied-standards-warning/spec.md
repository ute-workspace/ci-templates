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
- AC4: A missing caller checkout, or a failed caller checkout that leaves a directory behind, is reported as a visible "not checked" warning, not as clean.
  Verify: run `python3 -m unittest discover -s tests -v` → missing-checkout and failed-checkout cases pass.
- AC6: Summary paths cannot inject Markdown; symlinked `.agents`/`.claude`/skills paths and non-directory skills paths are reported, not followed, in every reusable workflow including the sparse deployment checkouts; no project name can hide another finding.
  Verify: run `python3 -m unittest discover -s tests -v` → summary-escaping, symlink, skill-name and `SparseCheckoutIntegrationTest` cases pass (real sparse checkout for `ansible-deploy.yml` and `gitops-image-promotion.yml`).
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

- Deployment workflows pass the caller checkout step's `outcome` to the check; anything but `success` is "not checked" (UND-57 review).
- Review dispositions (UND-57, UND-58): summary escaping, failed checkout, symlinks and a regular file named `skills` are fixed; actions pinned by tag and inputs interpolated into run scripts are pre-existing and out of scope.
- Review dispositions (UND-67, UND-68):
  - Symlinked `.agents`/`.claude` omitted by the deployment sparse checkout → fixed. Patterns add `/.agents` and `/.claude`, exclude their other children (`!/.agents/*`, `!/.claude/*`), and re-include only `core`/`skills`, so the parent link is checked out but unrelated caller files such as `.claude/settings.json` are not.
  - A skill named e.g. `x .agents y` hid `.agents/skills` → fixed. Skipping now matches only the fixed parent names recorded as symlinks, never names found in the project.
  - Bidi/control Unicode shown unchanged in summary and annotations → accepted, not changed. Names come from the caller repository, whose writers already control its CI; detection, finding count and the cleanup script (which acts on real paths) are unaffected, and ASCII controls are already entity-encoded in the summary. Faithful bidi neutralisation needs locale-aware decoding that the warning-only check does not justify; a regression test proves such names are still each reported and hide nothing.
- Detection uses only fixed paths in the caller project; no upstream source is fetched (UND-24 plan supersedes the earlier pinned-upstream draft).
- The check body is embedded in each workflow rather than fetched from this repository at run time, so no extra checkout, ref, or token is needed; a test keeps every copy identical to `scripts/check-copied-standards.sh`.
