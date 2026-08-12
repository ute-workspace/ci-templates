# Client deployment model without Jenkins

Use GitHub Actions for CI and release, but do not let a GitHub-hosted runner SSH
directly to the client production server.

For Docker Compose use a dedicated, client-approved self-hosted runner that:

- is not the application host;
- has only the required Ansible SSH key;
- is restricted to a GitHub Actions runner group;
- runs a protected GitHub Environment with required reviewers;
- invokes a pinned `ansible` tag.

For Kubernetes, use the release workflow to create a reviewed change in the
client GitOps repository; Argo CD applies it. Do not store kubeconfig in a
general CI secret when an in-cluster GitOps controller can reconcile safely.
