# CI/CD

This covers how the ci-templates repository validates itself
(`.github/workflows/validate.yml`). It is a distinct topic from the
reusable workflows this repository ships for other repositories to call —
see `docs/product-overview.md` for what those workflows do and
`docs/architecture.md` for their data flow and integrations.

## CI/CD model

`validate.yml` runs on pull requests (opened, synchronize, reopened,
ready_for_review) and on push to `main`. Its `yaml` job is skipped for
draft pull requests.

## Pipeline owner

CODEOWNERS governs required review; see `CODEOWNERS` at the repository
root.

## Build

There is no build step: this repository ships YAML workflow files and
Markdown docs, not compiled or bundled artifacts.

## Test

The `yaml` job parses every file under `.github/workflows/*.y*ml` with
PyYAML (`yaml.safe_load`) to catch malformed YAML. It does not execute the
workflows themselves or lint their semantics (no `actionlint`/`yamllint`
step is configured).

## Deployment

Nothing is deployed from this repository. A merge to `main` makes the
current workflow file content available to consumers pinned to a mutable
ref (e.g. `@main` or a moving major tag); consumers pinned to a commit SHA
or an existing tag are unaffected until they bump their pin. Tagging a
release (see `CHANGELOG.md`) is the only "release" action this repository
performs.

## Rollback

Revert the merge commit on `main`, or re-point the tag used by this
repository's own release process. Consumers pinned to a commit SHA are
unaffected by either action and roll back only by changing their own pin.

## Required credentials

`validate.yml` requires no repository secrets; it uses the default,
read-only `GITHUB_TOKEN` permission (`contents: read`) implicitly provided
by GitHub Actions. The reusable workflows this repository ships declare
their own required secrets (`ANSIBLE_PRIVATE_KEY`, `GHCR_USERNAME`,
`GHCR_TOKEN`, `RUNTIME_ENV_CONTENT`, `ANSIBLE_REPOSITORY_TOKEN`,
`GITOPS_REPOSITORY_TOKEN`); see `docs/architecture.md` (Security model) —
those are supplied by the calling/consumer repository, not this one.

## Local gates

Before opening or updating a PR, run the same YAML-parsing check the
`yaml` job runs. `actionlint` and `yamllint` are not installed in this
environment, so this Python/PyYAML snippet is the fallback used both here
and by the job itself:

```bash
python3 - <<'PY'
import pathlib, yaml
for path in pathlib.Path('.github/workflows').glob('*.y*ml'):
    yaml.safe_load(path.read_text())
PY
```

Run it from the repository root. No output means every workflow file
parsed successfully.
