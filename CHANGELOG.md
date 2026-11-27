# Changelog

Release notes of each `vX.Y.Z` tag; how a release is made:
[docs/release-process.md](docs/release-process.md).

## [Unreleased]

## [3.0.0] - 2026-11-27

A failed build provenance attestation now fails `container-release.yml`
and `node-container-release.yml`; a private repository whose GitHub plan
cannot store attestations sets `attest: skip` before moving to `@v3.0.0`.

### Breaking
- `container-release.yml` and `node-container-release.yml`: build
  provenance attestation is no longer best-effort. A failed attestation
  now fails the job (it was ignored with `continue-on-error`). A new
  `attest` input (`required`, the default, or `skip`) lets a private
  repository whose GitHub plan cannot store attestations opt out; `skip`
  reports the image as "Not attested" in a warning and the job summary.

### Changed
- `actions/attest-build-provenance` v4.2.2 and `actions/checkout` v7.0.1
  in every reusable workflow that uses them.

### Added
- Licensed under Apache-2.0 (`LICENSE`, `NOTICE`); copyright holder Under
  Tree Entertainment.

## [2.0.0] - 2026-11-20

The copied agent standards check now fails caller jobs; callers on `@v1`
stay on 1.0.0 until they move to `@v2.0.0` (or `@v2`).

### Breaking
- Every reusable workflow fails the job when the caller project contains
  copied agent standards (`.agents/core`, `.agent-standards.yml`,
  `.claude/skills`, `.agents/skills`); remove them with agent-standards'
  `scripts/clean-project.py` before moving to this release.

### Changed
- Third-party actions in every reusable workflow are pinned to commit SHAs
  of their current major releases.

### Added
- `docs/client-deployment.md`: rules for client development stacks on
  Docker Compose or Portainer Git stacks (local images, no host ports, dev
  servers behind the proxy with access control, on-demand services,
  secrets).

## [1.0.0] - 2026-08-15

The same commit as the `v1` tag.

### Added
- Reusable Node CI workflow (`node-ci.yml`): Node.js lint and test only,
  no image build or publish.
- Reusable Ansible Deploy workflow (`ansible-deploy.yml`): runs an Ansible
  playbook from an external, pinned Ansible repository on a self-hosted
  deployment runner.
- Reusable GitOps Image Promotion workflow (`gitops-image-promotion.yml`):
  opens a pull request in an external GitOps repository that updates a
  Kustomize image reference to an immutable digest.
- Reusable Container Release workflow (`container-release.yml`): builds a
  container image, pushes it to GHCR, and outputs an immutable
  digest-pinned image reference.
- Reusable Node Container Release workflow (`node-container-release.yml`):
  the same release flow with a Node.js install/lint/start/health-check/test
  pass before the image build.
- Trivy vulnerability scanning of the built image before it is pushed, in
  both release workflows; the job fails on HIGH/CRITICAL findings.
- `trivyignores` input on `container-release.yml` to point the scan at a
  consumer's own ignore file(s) when a Dockerfile lives outside the repo
  root.
- Best-effort build-provenance attestation (`actions/attest-build-provenance`)
  in both release workflows; it does not fail the release job if the
  attestation step errors.

### Fixed
- Both release workflows now record the digest actually returned by
  `docker push` as the release's `image-ref`, instead of the local
  build-time digest, so the recorded reference always resolves to the
  image that was actually published.

### Deployment notes
- Consumers pin `container-release.yml` / `node-container-release.yml` at
  `@v1`; see `docs/action-pinning.md` for the pinning policy.
