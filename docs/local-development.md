# Local development

Everything runs in containers. The only local prerequisites are Docker with the
Compose plugin and Git.

## First run

```bash
cp .env.example .env
docker compose -f compose.yaml -f compose.dev.yaml up --build
docker compose -f compose.yaml -f compose.dev.yaml ps
```

Open <http://localhost:8080>. The stack is ready when every service reports
`healthy`. The first build downloads the base images and resolves Python
dependencies from the committed lockfiles.

## Day-to-day

```bash
# start in the background
docker compose -f compose.yaml -f compose.dev.yaml up -d

# follow logs for one service
docker compose -f compose.yaml -f compose.dev.yaml logs -f backend

# stop everything, keep volumes
docker compose -f compose.yaml -f compose.dev.yaml down

# rebuild after changing a Dockerfile or a lockfile
docker compose -f compose.yaml -f compose.dev.yaml up -d --build
```

### Hot reload

- Backend: `uvicorn --reload` watches `/app/src`, which is bind-mounted from
  `backend/src`. Saving a module restarts the worker.
- Frontend: Flask's debug reloader watches `/app/src`, which is bind-mounted
  from `frontend/src`. Jinja2 templates reload without a process restart.

No image rebuild is needed for either. Windows users should prefer WSL2 for
the repository; Docker Desktop's Linux engine gives reliable file-watching and
much faster bind-mount I/O. If you run from a Windows path, the reloaders still
work but can take a few seconds longer.

### Database

PostgreSQL is not published to the host. Use the container:

```bash
docker compose -f compose.yaml -f compose.dev.yaml exec postgres \
  psql -U app -d app
```

Run migrations from inside the backend container:

```bash
docker compose -f compose.yaml -f compose.dev.yaml exec backend \
  alembic upgrade head
```

### Reset the local database

```bash
bash infra/reset-db.sh        # macOS, Linux, Git Bash
```

```powershell
.\infra\reset-db.ps1          # Windows PowerShell
```

Or, equivalently and without the helper:

```bash
docker compose -f compose.yaml -f compose.dev.yaml down
docker volume rm proy-nuevo_postgres_data
docker compose -f compose.yaml -f compose.dev.yaml up -d --wait
```

The helper removes only the PostgreSQL volume. Caddy's certificate and config
volumes are left intact.

## Environment variables

`.env.example` lists every variable the stack reads. At minimum, copy it and
replace the placeholder passwords and tokens. Compose refuses to start when a
required variable is missing, and names it in the error.

## Ports

Only the proxy is published, on `PROXY_PORT` (default `8080`). Backend,
frontend, and PostgreSQL are reachable only on the Compose network. To debug
the API directly, add a temporary `ports:` entry to `compose.dev.yaml` rather
than changing the base file.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `service "backend" is not running` during `exec` | The container exited; check `logs backend` |
| Frontend shows "Backend unavailable" | Backend unhealthy, wrong `DATABASE_URL`, or wrong service token |
| `bind source path does not exist` | Run Compose from the repository root |
| Reload does not fire on Windows | Move the checkout into WSL2 |
