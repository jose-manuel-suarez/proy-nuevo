# Continuous integration

The `ci` workflow runs on every pull request targeting `main` and on every push
to a `feature/**` branch.

## Jobs and required checks

The branch ruleset requires these check contexts. The names below are the job
identifiers in `.github/workflows/ci.yml`; renaming a job without updating
`infra/github/ruleset.sh` silently unblocks merges.

| Check context | What it proves | What a failure means |
| --- | --- | --- |
| `branch-name` | The head branch matches `feature/<kebab-case-name>` | Rename the branch; the merge stays blocked |
| `lint` | Ruff finds no lint or formatting violation | Fix the reported lines or run `ruff format` |
| `typecheck` | Mypy accepts both projects | Fix the type error; do not add blanket ignores |
| `backend-tests` | Pytest passes against a real PostgreSQL service | A behavior or migration assumption broke |
| `frontend-tests` | Pytest passes with the stubbed API transport | A template, view, or client contract broke |
| `migrations` | Alembic upgrades an empty database and reports no model drift | Add the missing migration or fix the failing one |
| `images (backend)` | The backend image builds | The Dockerfile or build context is broken |
| `images (frontend)` | The frontend image builds | The Dockerfile or build context is broken |

`smoke` is **not** a required check. It starts the full Compose stack, asserts
that the index page renders through Caddy, and checks readiness. It is gated by
a path filter because it is the slowest job: it runs only when backend,
frontend, Compose, or infrastructure files change.

## Path filters

Path filters live in the `changes` job, not in the workflow trigger. A filter on
the trigger would skip the entire workflow for a docs-only pull request, and
the required checks would then never report — leaving the pull request blocked
forever. Filtering optional jobs keeps every required check present and green
while skipping expensive work that cannot be affected.

## Caching

`astral-sh/setup-uv` caches the uv cache directory keyed by the hash of the
committed lockfiles (`backend/uv.lock`, `frontend/uv.lock`). A lockfile change
misses the cache intentionally; a source-only change hits it.

## Local equivalents

The workflow only orchestrates commands you can run yourself:

```bash
(cd backend && uv sync --frozen && uv run ruff check . && uv run mypy src && uv run pytest)
(cd frontend && uv sync --frozen && uv run ruff check . && uv run mypy src && uv run pytest)
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app \
  sh -c 'cd backend && uv run alembic upgrade head && uv run alembic check'
docker build -f backend/Dockerfile -t proy-nuevo-backend:ci .
docker build -f frontend/Dockerfile -t proy-nuevo-frontend:ci .
docker compose -f compose.yaml -f compose.dev.yaml up -d --build --wait
curl --fail http://localhost:8080/readyz
```
