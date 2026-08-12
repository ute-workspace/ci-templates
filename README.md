# ci-templates

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
