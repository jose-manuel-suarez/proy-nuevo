# Deployment

Production is a single VPS running Docker Compose behind Caddy. Images are
built and published by GitHub Actions, pulled by the host, and verified through
the public readiness endpoint.

## Prerequisites

- A VPS with Docker Engine and the Compose plugin, reachable over SSH.
- A DNS record for the production domain pointing at the VPS.
- Ports 80 and 443 open; port 22 reachable by the deploy user.
- A GitHub environment named `production`, ideally with required reviewers.

## GitHub configuration

Secrets:

| Secret | Purpose |
| --- | --- |
| `DEPLOY_HOST` | VPS hostname or IP |
| `DEPLOY_USER` | SSH user for deployment |
| `DEPLOY_SSH_KEY` | Private key for that user |
| `DEPLOY_KNOWN_HOSTS` | Pinned host key (`ssh-keyscan -H host`) |
| `DB_PASSWORD` | PostgreSQL password |
| `SERVICE_TOKEN` | Shared frontend-to-backend token |
| `SESSION_SECRET` | Flask session signing key |

Variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DOMAIN` | — | Public hostname served by Caddy |
| `POSTGRES_DB` | `app` | Database name |
| `POSTGRES_USER` | `app` | Database user |
| `DEPLOY_DIR` | `/opt/proy-nuevo` | Deployment directory on the host |

The deploy workflow validates every required value before it opens an SSH
connection, so a missing secret fails the job without touching the host.

Packages are private by default. The deploy job passes a short-lived registry
token to the host for the pull. If the packages are made public, the host login
can be removed.

## First deployment

1. Merge the bootstrap change into `main`.
2. Apply the ruleset (`./infra/github/ruleset.sh`) once CI has run on `main`.
3. Run the `deploy` workflow manually with `image_tag` set to the short or full
   merge commit SHA. Images are published as `sha-<value>`.
4. The workflow copies Compose files and `infra/` to the host, creates the
   deployment directory, network, and environment file, then runs
   `infra/deploy.sh`.

The first deploy creates the database volume empty. The baseline migration runs
before the application containers start.

## What a deployment does

```text
 build + push images (sha)  ->  copy release files  ->  write .env atomically
        ->  docker compose pull  ->  alembic upgrade head (one-off container)
        ->  docker compose up -d  ->  poll https://$DOMAIN/readyz
        ->  success: record .current_tag     failure: redeploy previous tag
```

- Deployments are serialized by a concurrency group; a second release waits.
- Migrations run in a one-off container and never on application startup.
- A failed migration aborts before any application container is replaced.
- A failed health check restores the previous image tag automatically.
- Rollback never reverses the schema; migrations must remain compatible with
  the previous release (expand/contract).

## Manual rollback

```bash
ssh deploy@<host>
cd /opt/proy-nuevo
./infra/rollback.sh
```

The command redeploys the tag recorded in `.previous_tag` and completes without
building an image. After a rollback, `.previous_tag` holds the faulty release,
so the same command can move forward again.

## Migration failure drill

To rehearse the failure path without production traffic:

1. Create a branch with a migration that raises on upgrade.
2. Let CI pass (the migration job runs against an empty database and fails, so
   instead break it in a way that only fails with existing data, or dispatch
   manually from a checkout with a broken revision).
3. Dispatch `deploy` with that merge SHA.
4. Confirm the job fails, the migration container logs the error, and the
   previously running application containers are still serving.

The deployment script refuses to start new containers while migrations are
failing, which is the property this drill proves.

## Post-deploy failure drill

1. Deploy a known-good tag and confirm `/readyz` is green.
2. Deploy a tag whose application fails readiness (for example, the wrong
   `DATABASE_URL` baked into the environment).
3. Confirm the deployment fails and the previous tag is restored and serving.

## Secret rotation

1. Update the secret in the `production` GitHub environment.
2. Re-run the `deploy` workflow with the currently deployed tag.
3. The workflow rewrites the host environment file atomically and restarts the
   affected containers. No image is rebuilt.

## Port surface

Only Caddy publishes ports (80 and 443). The backend, frontend, and PostgreSQL
are reachable only on the Compose network. Verify from outside:

```bash
curl -fsS https://$DOMAIN/readyz
nc -zv <host> 5432    # must fail
nc -zv <host> 8000    # must fail
```

## Known limitations

- A single host is a single point of failure; there is no automated off-host
  database backup yet.
- A deployment replaces containers sequentially, so a short window of degraded
  service is possible; Caddy retries upstreams.
- The Caddy data volume holds certificates and must be preserved across
  deployments.
