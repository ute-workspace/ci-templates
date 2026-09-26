# Changelog

## Release v1

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

### Changed
### Known issues
### Deployment notes
- Consumers pin `container-release.yml` / `node-container-release.yml` at
  `@v1`; see `docs/action-pinning.md` for the pinning policy.
