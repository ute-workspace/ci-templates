# CI/CD

This covers how the ci-templates repository validates itself
(`.github/workflows/validate.yml`). It is a distinct topic from the
reusable workflows this repository ships for other repositories to call —
see `docs/product-overview.md` for what those workflows do and
`docs/architecture.md` for their data flow and integrations.

## CI/CD model

`validate.yml` runs on pull requests (opened, synchronize, reopened,
ready_for_review) and on push to `main`. Its `yaml` and `tests` jobs are
skipped for draft pull requests.

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

The `tests` job runs `python3 -m unittest discover -s tests -v`.
`tests/test_copied_standards.py` covers the copied agent standards check
(clean, individual, multiple, and both-skill-directory findings, a missing
caller checkout, annotation escaping) and its integration in every reusable
workflow: the embedded step matches `scripts/check-copied-standards.sh`,
runs after a checkout of the caller project, and fails with `::error`
annotations on findings, while a failed caller checkout only warns.
For the two deployment workflows it also makes a real non-cone sparse
checkout of a fixture Git repository with the workflow's own patterns, then
runs the embedded step, so symlinked `.agents`/`.claude` parents are proven
to reach the check and unrelated caller files are proven not to be checked
out. These tests need `git`.

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

Then run the tests the `tests` job runs (needs Python 3 with PyYAML, and
bash):

```bash
python3 -m unittest discover -s tests -v
```

Run both from the repository root. No output from the first means every
workflow file parsed successfully.

After changing `scripts/check-copied-standards.sh`, copy its body (without
the leading `#` comment lines) into the "Check for copied agent standards"
step of every reusable workflow; the tests fail until all copies match.
