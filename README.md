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

## Build provenance of released images

`container-release.yml` and `node-container-release.yml` take an `attest`
input:

- `required` (default): attest the pushed image digest with
  `actions/attest-build-provenance`; the job fails when the attestation
  fails or does not run. Earlier releases ignored that failure.
- `skip`: no attestation; a "Not attested" warning and job summary say so.
  Use it for a private repository whose GitHub plan cannot store
  attestations ("Feature not available ... make this repository public").

The caller grants `packages: write`, `attestations: write` and
`id-token: write` in both modes. The image is pushed before it is
attested, so after a failed attestation its tags already point to an
unattested image; the job summary names it. With `skip`, the run log, the
pushed digest and the image's OCI labels trace the image to its commit,
but nothing makes that independently verifiable.

```yaml
jobs:
  release:
    uses: ute-workspace/ci-templates/.github/workflows/container-release.yml@<commit SHA> # v3.0.0
    with:
      image-name: YOUR_ORG/YOUR_IMAGE
      attest: skip   # private repository on a plan without attestations
```

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

## License

Copyright 2026 Under Tree Entertainment. Licensed under the
[Apache License, Version 2.0](LICENSE); see [NOTICE](NOTICE).
