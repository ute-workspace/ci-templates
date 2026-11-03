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

## Development stacks on Compose or Portainer Git stacks

Client development environments that run as Docker Compose stacks, including
Portainer Git stacks that redeploy on every commit, follow these rules.

### Locally built images

Set `pull_policy: never` on every service whose image is built on the host and
exists in no registry. A Git-stack redeploy pulls each image; without this
setting the pull fails and the redeploy is retried on every sync cycle.

```yaml
services:
  api:
    image: example-api:latest
    pull_policy: never
```

### No host ports

Publish no host ports (`ports:`). Each web service joins the reverse proxy
network and is reached only by its domain through the proxy (for example a
Traefik router with TLS). Host ports of different projects on one host
collide.

### Dev servers behind the proxy

Vite, webpack-dev-server and the Angular dev server reject requests whose
`Host` header is not in their allowed list. Use one of:

- the proxy does not forward the original host, so the dev server receives
  the container address (Traefik:
  `traefik.http.services.<name>.loadbalancer.passhostheader=false`);
- the project adds the domain to the framework's allowed hosts
  (`server.allowedHosts` in Vite, `allowedHosts` in webpack-dev-server or in
  `angular.json` serve options). Angular's Vite-based dev server ignores
  `--disable-host-check`.

### On-demand services

Development services that are started only when needed use `restart: "no"`.
The stack sync then does not report them as stopped or drifted.
Long-running services keep `restart: unless-stopped`.

### Secrets

- Secrets stay in the project's git-ignored `.env`; they are never committed
  to the application repository or to the stack repository.
- The `.env` file is bind-mounted read-only and read by the service at start:

  ```yaml
  services:
    api:
      volumes:
        - type: bind
          source: /path/to/project/.env
          target: /run/app.env
          read_only: true
      command:
        - sh
        - -c
        - set -a && . /run/app.env && set +a && exec node server.js
  ```

- Compose files contain no literal credentials. A database service with
  `MYSQL_ROOT_PASSWORD: admin` (or any other fixed password) in the compose
  file is an anti-pattern: the password is committed, shared by every
  environment and cannot be rotated without a commit.
