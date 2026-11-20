# Agent notes

- Install: Python 3 with PyYAML, `git`, `bash`, `pre-commit`; no build step.
- Test: `python3 -m unittest discover -s tests -v` (33 tests, about 1 s); `pre-commit run --all-files` for linters.
- actionlint's pre-commit hook runs shellcheck only when `shellcheck` is on PATH; CI's runner has it, so check with `docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:1.7.12 .github/workflows/*.yml`.
- Action pins: resolve a tag's commit with `git ls-remote <repo> 'refs/tags/<tag>*'` and take the `^{}` line for an annotated tag.
- Renovate's lookup of `aquasecurity/trivy-action` fails (`no-result`) although the tag exists; cause not verified (runner in dev-automation).
- SonarQube is internal: GitHub-hosted runners cannot reach it.
