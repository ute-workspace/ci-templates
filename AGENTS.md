# ci-templates

Public, versioned reusable GitHub Actions workflows (`workflow_call`) for
internal and client repositories. This repository owns the GitHub Actions
pipeline implementation; Jenkins shared steps live in `jenkins-library`.

## Stack and layout

- `.github/workflows/` — the five reusable workflows (`container-release.yml`,
  `node-container-release.yml`, `node-ci.yml`, `ansible-deploy.yml`,
  `gitops-image-promotion.yml`) and `validate.yml`, this repository's own CI.
- `scripts/check-copied-standards.sh` — canonical copied agent standards
  check, embedded verbatim in every reusable workflow.
- `tests/` — Python `unittest` unit and workflow integration tests.
- `examples/` — caller workflows; `docs/` — product overview, architecture,
  CI/CD, action pinning, client deployment.
- No build step and no deployment: the repository ships YAML and Markdown.

## Commands

Run from the repository root; needs Python 3 with PyYAML, `git` and `bash`.

```bash
# Workflow YAML validation (no output means every file parsed)
python3 - <<'PY'
import pathlib, yaml
for path in pathlib.Path('.github/workflows').glob('*.y*ml'):
    yaml.safe_load(path.read_text())
PY

# Unit and workflow integration tests
python3 -m unittest discover -s tests -v
```

`actionlint` and `yamllint` are not configured.

## Gates

- Run both commands above before opening a PR or marking it ready.
- `validate.yml` runs the same `yaml` and `tests` jobs on pull requests and
  on push to `main`; both jobs are skipped while a PR is a draft.
- `CODEOWNERS` governs required review.

## Project rules

- The repository is public: no secrets, internal network topology or
  customer configuration (`SECURITY.md`). Consumers supply their own
  secrets, GitHub Environment protections and deployment runners.
- Consumers pin a tag or commit SHA; a merge to `main` reaches only callers
  on a mutable ref. Treat workflow inputs, outputs, secrets and permissions
  as a public interface and document changes in `docs/architecture.md`,
  `docs/product-overview.md` and `examples/`.
- Third-party actions follow `docs/action-pinning.md`.
- After changing `scripts/check-copied-standards.sh`, copy its body (without
  the leading `#` comment lines) into the "Check for copied agent standards"
  step of every reusable workflow; the tests fail until all copies match.
  The check stays warning-only; the `.agents/core`, `.agent-standards.yml`,
  `.claude/skills` and `.agents/skills` paths it names are what it detects
  in caller projects.
- Changes to `validate.yml` are documented in `docs/ci-cd.md`.
- `CHANGELOG.md` is for releases only.
