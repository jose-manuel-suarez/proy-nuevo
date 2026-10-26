# proy-nuevo

Two independently deployable applications behind a single edge proxy:

- `backend/` — FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic.
- `frontend/` — Flask 3, Jinja2, HTMX, server-side rendering.
- PostgreSQL for persistence, Caddy as the edge proxy.
- Everything runs in containers: application code, database, and proxy.

The browser only talks to the frontend. The frontend calls the backend over the
internal container network using a shared service token.

## Repository layout

```
backend/            FastAPI application, migrations, tests, image definition
frontend/           Flask application, templates, static assets, tests
infra/              deployment scripts, Caddy configuration, GitHub settings
docs/               local workflow, CI, deployment, and Git workflow guides
compose.yaml        shared service graph
compose.dev.yaml    local overrides: bind mounts, reload, debug
compose.prod.yaml   production overrides: published images, no source mounts
openspec/           change proposals, specs, and task tracking
```

## Prerequisites

- Docker Desktop (or Docker Engine with the Compose plugin), running.
- Git.
- `uv` for running the Python projects outside containers (optional but needed
  for tests, linting, and migrations against a local database).

Windows users get the best file-watching behavior inside WSL2; see
`docs/local-development.md`.

## Quick start

```bash
git clone <repository-url>
cd proy-nuevo
cp .env.example .env
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Wait until `docker compose ps` reports every service healthy, then open
<http://localhost:8080>. The page shows the backend status fetched through the
frontend. Code changes under `backend/src` and `frontend/src` reload without a
rebuild.

Stop the stack with `Ctrl+C`, or in the background:

```bash
docker compose -f compose.yaml -f compose.dev.yaml down
```

Reset only the local database:

```bash
docker compose -f compose.yaml -f compose.dev.yaml down
docker volume rm proy-nuevo_postgres_data
```

Full guides: [local development](docs/local-development.md),
[CI](docs/ci.md), [deployment](docs/deployment.md), and
[the change workflow](docs/workflow.md).

## Development workflow

Every change is developed on `feature/<change-name>`, verified by CI, archived
on that branch, and merged through a pull request. A pull request merges only
when the `archive` label is applied — the label is the sole merge
authorization. Direct pushes to `main` are rejected for everyone.
