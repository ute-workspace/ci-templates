# Product overview

ci-templates is a reusable CI/CD workflow library for GitHub Actions:
other repositories call its workflows with `workflow_call` instead of
duplicating build/scan/release/deploy logic in their own `.github/workflows/`.

## Purpose

Give internal and client repositories a single, reviewed place to get
container image builds, vulnerability scanning, GHCR publishing, Ansible
deployment, and GitOps image promotion, so each consumer repository stays
thin and any fix or policy change (e.g. Trivy severity gating) is made once
and picked up by every caller at its next pin bump.

## Users

Other repositories in this GitHub organization (and, per `README.md`,
external client repositories) that reference these workflows by tag or
commit SHA from their own `.github/workflows/*.yml` files. See
`examples/*.yml` for the exact caller syntax.

## Main workflows

- `container-release.yml` — generic build/scan/publish for a container
  image.
- `node-container-release.yml` — same, with a Node.js
  install/lint/test/health-check pass before the image build.
- `node-ci.yml` — Node.js lint/test only, no image build or publish.
- `ansible-deploy.yml` — runs an Ansible playbook from an external,
  pinned Ansible repository against a self-hosted deployment runner.
- `gitops-image-promotion.yml` — opens a pull request in an external
  GitOps repository that updates a Kustomize image reference to an
  immutable digest.

Full behavior and data flow: `docs/architecture.md`. Pinning policy:
`docs/action-pinning.md`. Deployment topology guidance for consumers:
`docs/client-deployment.md`.

## Non-goals

- Not an application or a runtime service; it has no deployment of its
  own beyond being consumed as workflow files (see `docs/ci-cd.md`, which
  covers the repository's own validation pipeline).
- Does not store or manage any client's network topology, secrets, or
  GitHub Environment configuration — those stay in the consuming repo.
- Does not apply manifests to a Kubernetes cluster; `gitops-image-promotion.yml`
  only opens a pull request in the GitOps repository.
- Does not SSH from a GitHub-hosted runner to a production host; Ansible
  deployment requires a dedicated, client-approved self-hosted runner.

## Current status

Five reusable workflows are published (`container-release.yml`,
`node-container-release.yml`, `node-ci.yml`, `ansible-deploy.yml`,
`gitops-image-promotion.yml`), each with a matching example caller under
`examples/`. The repository has one tagged release line, `v1`.
