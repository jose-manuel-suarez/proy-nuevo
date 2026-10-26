# Infrastructure

Deployment scripts, Caddy configuration, and GitHub settings for the
production host. Local development lives in the root Compose files; see
`docs/local-development.md`.

## Images

Both images build from the repository root because the build context spans
`backend/`, `frontend/`, and the shared ignore rules.

```bash
SHA=$(git rev-parse --short=7 HEAD)
OWNER=your-github-user
REPO=your-repository

docker build -f backend/Dockerfile \
  -t "ghcr.io/$OWNER/$REPO-backend:sha-$SHA" .

docker build -f frontend/Dockerfile \
  -t "ghcr.io/$OWNER/$REPO-frontend:sha-$SHA" .
```

Tag convention:

| Tag | Meaning |
| --- | --- |
| `sha-<7 chars>` | Immutable release tag derived from the commit; the only tag deployed |
| `latest` | Never published by this pipeline; do not use it for deployment |

A deployment records the running tag on the host in `.current_tag` and keeps
the previous one in `.previous_tag`. Rollback redeploys `.previous_tag`; no
image is rebuilt.

## Contents

```
deploy.sh            pull, migrate, rollout, verify, roll back on failure
rollback.sh          redeploy the recorded previous tag
host-bootstrap.sh    create deployment directory, network, env file once
caddy/Caddyfile.dev  local HTTP proxy
caddy/Caddyfile.prod automatic HTTPS for $DOMAIN
github/ruleset.sh    apply branch protection and merge settings
```

Scripts are POSIX shell and expect Docker with the Compose plugin on the host.
`deploy.sh` and `rollback.sh` are also exercised from the `deploy` workflow.
