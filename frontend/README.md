# Frontend

Flask 3 application with Jinja2 templates and HTMX, rendered entirely on the
server. It is the only public application: the browser never calls the backend
directly.

## Commands

All commands run from `frontend/`.

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run flask --app app.main run --debug --port 5000
```

Flask detects the `create_app` factory automatically. Outside containers the
process needs `SECRET_KEY`, `SERVICE_TOKEN`, and `BACKEND_URL` in the
environment (or a `.env` next to the working directory).

## Environment variables

| Variable | Required | Meaning |
| --- | --- | --- |
| `SECRET_KEY` | yes | Flask session signing key |
| `SERVICE_TOKEN` | yes | Shared secret sent to the backend as `X-Service-Token` |
| `BACKEND_URL` | yes | Internal backend base URL, e.g. `http://backend:8000` |
| `REQUEST_TIMEOUT` | no | Upstream timeout in seconds (default `5`) |
| `APP_ENV` | no | Environment label (default `development`) |

## Templates and static assets

- `src/app/templates/base.html` — document shell and local asset references.
- `src/app/templates/index.html` — status page and HTMX refresh button.
- `src/app/templates/partials/status.html` — fragment swapped into `#status`.
- `src/app/static/htmx.min.js` — HTMX 2.0.4, vendored.
- `src/app/static/app.css` — plain CSS, no build step.

Static policy: no CDN and no JavaScript toolchain. The page must render
without any third-party network request, which the test suite asserts.

## Routes

- `GET /` — status page.
- `GET /partials/status` — HTMX fragment with a fresh status read.
- `GET /healthz` — process liveness.
- `GET /readyz` — readiness, includes reaching the backend; 503 when it fails.
