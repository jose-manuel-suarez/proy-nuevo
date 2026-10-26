# Backend

FastAPI application with Pydantic v2 settings, async SQLAlchemy 2, and Alembic
migrations. The API is reachable only from the frontend container.

## Commands

All commands run from `backend/`. `uv sync` installs the development
environment, including test, lint, and type-check tooling.

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run uvicorn app.main:create_app --factory --reload --port 8000
```

The integration test that checks a live database is opt-in:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://app:pass@localhost:5432/app_test uv run pytest -m integration
```

## Environment variables

| Variable | Required | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | yes | Async SQLAlchemy URL, e.g. `postgresql+asyncpg://user:pass@host:5432/db` |
| `SERVICE_TOKEN` | yes | Shared secret required on every `/api/v1` request |
| `APP_ENV` | no | Environment label exposed by `/api/v1/info` (default `development`) |
| `LOG_LEVEL` | no | Log level (default `INFO`) |

`Settings` has no defaults for `DATABASE_URL` and `SERVICE_TOKEN`: a missing
value raises a `ValidationError` at startup.

## Migrations

```bash
uv run alembic upgrade head
uv run alembic check        # fails when the models drift from the schema
uv run alembic revision --autogenerate -m "describe the change"
```

The baseline revision is intentionally empty; the first domain model arrives
in a later change.

## Endpoints

- `GET /healthz` — process liveness, no dependencies.
- `GET /readyz` — readiness, verifies the database; 503 when it is unavailable.
- `GET /api/v1/info` — service metadata; requires `X-Service-Token`.
