# ci-templates

[![](https://img.shields.io/badge/python-3.13-green)](https://www.python.org/) [![](https://img.shields.io/badge/actionlint-1.7.12-green)](https://github.com/rhysd/actionlint) [![](https://img.shields.io/badge/yamllint-1.38.0-green)](https://yamllint.readthedocs.io/) [![](https://img.shields.io/badge/shellcheck-0.11.0-green)](https://www.shellcheck.net/) [![](https://img.shields.io/badge/ruff-0.17.6-green)](https://docs.astral.sh/ruff/) ![](https://img.shields.io/badge/cleanup-2026--11--20-blue) [![](https://img.shields.io/badge/repo--cleanup--audit-v1.0.0-blueviolet)](https://github.com/ute-workspace/agent-standards/blob/04ac8cd3158f75fefc8bd5986f58706af005ab63/skills/repo-cleanup-audit/SKILL.md) <!-- repo-cleanup-audit -->

Public, versioned reusable GitHub Actions workflows for internal and client repositories.

The repository contains generic CI/CD code only: no internal network topology, no
customer configuration and no secrets. Client projects keep their own GitHub
Environment protections, secrets and deployment runners.

## Supported client paths

```text
GitHub-hosted runner → lint/test/build/container publish
GitHub Environment + client self-hosted deployment runner → Ansible
GitHub-hosted runner → GitOps pull request → client/internal Argo CD

`gitops-image-promotion.yml` changes an immutable image reference and opens a GitOps pull request; it never applies manifests directly to a cluster.
```

Use immutable tags or commit SHAs when calling reusable workflows. `v1` is a
convenience major line; sensitive production workflows should pin a commit SHA.

## Development

Needs Python 3 with PyYAML, `git`, `bash` and [pre-commit](https://pre-commit.com/).

```bash
pre-commit install                         # run the hooks on every commit
pre-commit run --all-files                 # hygiene hooks, gitleaks, yamllint, actionlint, shellcheck, ruff
python3 -m unittest discover -s tests -v   # unit and workflow integration tests
```

`validate.yml` runs the same checks on pull requests that are not drafts and
on push to `main`;
see [docs/ci-cd.md](docs/ci-cd.md).
