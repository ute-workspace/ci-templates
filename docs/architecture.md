# Architecture

## Overview

This repository is a library of reusable GitHub Actions workflows
(`workflow_call`) plus example caller workflows. It ships no application
code and no runtime service; consumers reference a workflow file at a tag
or commit SHA and pass inputs/secrets to it. See `docs/product-overview.md`
for purpose and users.

## Components

- `.github/workflows/container-release.yml` — builds a container image,
  scans it with Trivy, pushes it to GHCR, and emits an immutable
  `image-ref` (digest-pinned) output.
- `.github/workflows/node-container-release.yml` — same release flow as
  `container-release.yml`, plus a Node.js install/lint/start/health-check/test
  pass before the image is built.
- `.github/workflows/node-ci.yml` — Node.js CI only: install, lint, and an
  optional start/health-check/test pass. No image is built or published.
- `.github/workflows/ansible-deploy.yml` — checks out a pinned ref of an
  external Ansible repository and runs a playbook against an inventory path
  that lives on the self-hosted runner, using a private SSH key from
  secrets.
- `.github/workflows/gitops-image-promotion.yml` — checks out an external
  GitOps repository, updates a Kustomize image reference to an immutable
  digest, validates the rendered manifests, and opens a pull request there.
  It never applies manifests to a cluster directly.
- `.github/workflows/validate.yml` — this repository's own CI; see
  `docs/ci-cd.md`.
- `docs/action-pinning.md` — third-party action pinning policy.
- `docs/client-deployment.md` — deployment topology guidance for
  consumers (Compose via self-hosted runner, or Kubernetes via GitOps).
- `examples/*.yml` — example caller workflows showing how a consumer repo
  invokes each reusable workflow.

## Data flow

Container release (`container-release.yml`, `node-container-release.yml`):
checkout -> (Node install/lint/start/health-check/test, node variant only)
-> login to GHCR -> compute tags/labels (`docker/metadata-action`) -> build
image locally (`push: false, load: true`) -> Trivy scan of the local image
(fails the job on HIGH/CRITICAL findings, `trivyignores` narrows this on
`container-release.yml`) -> `docker push --all-tags` -> parse the pushed
digest from `docker push`'s own output -> emit `image-ref` as
`ghcr.io/<image-name>@sha256:...` -> best-effort build-provenance
attestation (`continue-on-error: true`).

Ansible deploy: install a private SSH key from secrets -> checkout a
pinned ref of the external Ansible repository -> install its pinned
Ansible Galaxy collections -> run the named playbook against the given
inventory path, passing GHCR and runtime-env secrets through as needed.

GitOps promotion: checkout the external GitOps repository -> set the image
reference in a Kustomize overlay to the caller-supplied digest -> build the
kustomization to validate it renders -> commit, push a promotion branch,
and open a pull request in the GitOps repository for review.

## External integrations

- **GHCR (`ghcr.io`)** — image registry; both release workflows log in
  with `GITHUB_TOKEN` and push there.
- **Trivy** (`aquasecurity/trivy-action`) — vulnerability scan of the
  locally built image before it is pushed.
- **`actions/attest-build-provenance`** — build provenance attestation,
  best-effort (`continue-on-error: true`).
- **Node.js / npm** (`actions/setup-node`) — install, lint, start, and test
  a Node.js application before building its image (`node-ci.yml`,
  `node-container-release.yml`).
- **External Ansible repository** — a separate, pinned repository checked
  out at deploy time; not vendored here.
- **External GitOps repository + Kustomize** — a separate repository whose
  Kustomize overlays this workflow edits and opens a PR against.
- **Argo CD** (consumer-side, not invoked by this repo) — expected to
  reconcile the GitOps repository after a promotion PR merges; see
  `docs/client-deployment.md`.

## Environments

This repository defines no environments of its own. Consumers supply a
GitHub Environment name via `deployment-environment` (`ansible-deploy.yml`,
`gitops-image-promotion.yml`) to gate deployment/promotion behind GitHub's
own environment protection rules (e.g. required reviewers).

## Security model

- `ansible-deploy.yml` requires `runner-label` to identify a dedicated
  deployment runner that is documented as never the application host
  itself.
- Secrets (`ANSIBLE_PRIVATE_KEY`, `GHCR_USERNAME`, `GHCR_TOKEN`,
  `RUNTIME_ENV_CONTENT`, `ANSIBLE_REPOSITORY_TOKEN`, `GITOPS_REPOSITORY_TOKEN`)
  are declared as reusable-workflow `secrets:` inputs; the workflow files
  never contain literal credential values.
- Container release jobs fail on HIGH/CRITICAL Trivy findings unless
  suppressed via `trivyignores`.
- GHCR login in the release workflows uses the ambient `GITHUB_TOKEN`, not
  a separate stored credential.
- See `docs/action-pinning.md` for the third-party action pinning policy
  and `docs/client-deployment.md` for the recommended deployment topology
  (no direct SSH from a GitHub-hosted runner to a production host;
  GitOps instead of a stored kubeconfig for Kubernetes targets).

## Deployment model

This repository is not deployed; it is consumed by reference
(`uses: ute-workspace/ci-templates/.github/workflows/<file>.yml@<ref>`).
See `docs/client-deployment.md` for how consumers wire these workflows to
their own Compose or Kubernetes targets, and `examples/*.yml` for concrete
caller syntax.

## Observability

Each reusable workflow's own job log is the only observability surface;
there is no separate logging/metrics/tracing integration. The container
release workflows print the parsed pushed digest and the Trivy scan
results to the job log.

## Known limitations

- Build-provenance attestation is best-effort: it does not fail the job on
  error, so a consumer relying on attestations must check that step's
  outcome separately.
- `gitops-image-promotion.yml` validates that the kustomization renders,
  but does not verify that Argo CD (or another controller) actually
  reconciles the resulting change.

## Constraints

- `docker push`'s own output, not `docker/build-push-action`'s
  build-time digest output, is the source of truth for the digest recorded
  in `image-ref`, because the release build step uses `push: false, load:
  true` (so Trivy/tests can inspect the local image first) and the actual
  registry push is a separate `docker push` step; the two can produce
  different manifest digests for the same local image.
- `trivyignores` paths are resolved relative to the repo root (the
  runner's working directory), not relative to a Dockerfile in a
  subdirectory; callers whose Dockerfile lives in a subdirectory must pass
  an explicit path.

## Exceptions

None currently tracked for this repository.
