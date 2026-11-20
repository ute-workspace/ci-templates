# Changelog

Release notes of each `vX.Y.Z` tag; how a release is made:
[docs/release-process.md](docs/release-process.md).

## [Unreleased]

Planned as `v2.0.0`: the copied agent standards check now fails caller jobs.

### Breaking
- Every reusable workflow fails the job when the caller project contains
  copied agent standards (`.agents/core`, `.agent-standards.yml`,
  `.claude/skills`, `.agents/skills`); remove them with agent-standards'
  `scripts/clean-project.py` before moving to this release.

### Changed
- Third-party actions in every reusable workflow are pinned to commit SHAs
  of their current major releases.
- `node-container-release.yml` writes its smoke-test log to
  `/tmp/node-release.log`.

## [1.0.0] - 2026-08-15

The same commit as the `v1` tag.


### Added
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
