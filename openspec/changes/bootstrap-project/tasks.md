# Tasks

## 1. Repository foundation

- [x] 1.1 Initialize the git repository and create the `backend/`, `frontend/`, `infra/`, and `docs/` directory layout; verify the tree matches the proposal and that `git status` is clean after the initial commit on `feature/bootstrap-project`.
- [x] 1.2 Add `.gitignore`, `.dockerignore`, and `.env.example` covering every variable the stack reads; verify no real credential is present and that `.env.example` lists database, service-token, proxy, and Python settings.
- [x] 1.3 Write the root `README.md` sections for prerequisites, quick start, and repository layout; verify a reader can follow the quick start without consulting other files.

## 2. Backend application

- [x] 2.1 Create `backend/pyproject.toml` with uv, Python 3.12, and pinned FastAPI, Pydantic v2, SQLAlchemy 2, asyncpg, Alembic, and pytest dependencies; verify `uv sync` succeeds and imports FastAPI, Pydantic, and SQLAlchemy.
- [x] 2.2 Implement settings loading through `pydantic-settings` with required variables and no fallback secrets; verify a test asserts that a missing required variable raises at startup.
- [x] 2.3 Implement the application factory, async engine and session lifecycle, and `/healthz` plus `/readyz` endpoints; verify `/healthz` returns 200 without a database and `/readyz` returns 503 when the database is unreachable.
- [x] 2.4 Initialize Alembic with the async template and create a baseline revision; verify `alembic upgrade head` succeeds on an empty database and `alembic check` reports no pending model change.
- [x] 2.5 Add backend pytest coverage for settings, health endpoints, and session dependency override; verify `uv run pytest` passes against a local PostgreSQL instance.
- [x] 2.6 Document backend commands and environment variables in `backend/README.md`; verify each documented command runs from a clean checkout with `uv sync`.

## 3. Frontend application

- [x] 3.1 Create `frontend/pyproject.toml` with uv, Python 3.12, Flask 3, Jinja2, httpx, and pytest; verify `uv sync` succeeds and the Flask app imports.
- [x] 3.2 Implement the Flask factory, configuration, and an API client that sends the service token, enforces a timeout, and surfaces upstream failures as a controlled error state; verify the client test covers success, timeout, and non-2xx responses.
- [x] 3.3 Implement the base and index templates plus the HTMX fragment flow, with HTMX vendored under `frontend/static/`; verify the page renders locally and requests no third-party asset at runtime.
- [x] 3.4 Add `/healthz` and `/readyz` to the frontend, where readiness includes reaching the backend; verify readiness returns 503 when the stubbed backend is unavailable.
- [x] 3.5 Add frontend pytest coverage with Flask's test client and a stubbed HTTP transport; verify template rendering, HTMX fragment responses, and upstream-error rendering pass.
- [x] 3.6 Document frontend commands, templates, and static asset policy in `frontend/README.md`; verify each documented command runs.

## 4. Container images

- [x] 4.1 Write the backend multi-stage Dockerfile with a non-root user, lockfile-based installation, health check on `/healthz`, and exec-form entrypoint; verify the image starts, the process is non-root, and the health check turns healthy.
- [x] 4.2 Write the frontend multi-stage Dockerfile with the same contract; verify the image starts, serves the index page, and reports healthy.
- [x] 4.3 Verify both runtime images exclude development tooling by running `pytest` and `ruff` inside them and confirming the commands are unavailable.
- [x] 4.4 Confirm signal handling by stopping each container while it serves a request; verify the process exits successfully inside the grace period without a forced kill.
- [x] 4.5 Verify no secret reaches an image by building with a populated `.env` present and inspecting image history and environment; confirm no credential value appears.
- [x] 4.6 Document the build command and the commit-SHA tagging convention in `infra/README.md`; verify one manual build produces the documented tag shape.

## 5. Local development stack

- [x] 5.1 Write `compose.yaml` with PostgreSQL, backend, frontend, and Caddy services, health checks, and an internal network; verify `docker compose up` brings every service to healthy.
- [x] 5.2 Write `compose.dev.yaml` with bind mounts, reload commands, and debug-only port publishing; verify editing a backend module and a Jinja2 template is reflected without rebuilding images.
- [x] 5.3 Add the Caddy development configuration and verify the rendered page is reachable on the single published proxy port while PostgreSQL and backend ports are not published by default.
- [x] 5.4 Add the database reset command to the Makefile or documented script and verify it reinitializes the database without affecting other volumes.
- [x] 5.5 Verify the missing-variable failure mode by removing a required value from the local environment file; confirm startup fails and names the variable.
- [x] 5.6 Document the local workflow, the reset procedure, and the WSL2 recommendation in `docs/local-development.md`; verify every documented command succeeds on a fresh clone.

## 6. Continuous integration

- [ ] 6.1 Add the CI workflow skeleton with pinned action versions and path filters; verify a pull request triggers it and a push to a feature branch triggers it.
- [x] 6.2 Add the lint and type-check jobs using ruff and mypy; verify an injected lint violation and an injected type error each fail the corresponding job.
- [x] 6.3 Add the backend test job with a PostgreSQL service container and a per-run database; verify the job passes and fails when a backend test is deliberately broken.
- [x] 6.4 Add the frontend test job; verify it fails when a tested template is broken.
- [x] 6.5 Add the migration consistency job that upgrades an empty database and runs `alembic check`; verify it fails when a model change has no migration.
- [x] 6.6 Add the image build job for both applications with no registry login; verify both images build and no package is published.
- [x] 6.7 Add the Compose smoke job that starts the built stack and asserts the index page renders through the proxy; verify it fails when the frontend cannot reach the backend.
- [ ] 6.8 Add dependency caching keyed by lockfile hash; verify a second run reports a cache hit for both Python projects.
- [x] 6.9 Document in `docs/ci.md` which jobs are required checks and what each failure means; verify the names match the workflow job identifiers exactly.

## 7. Host preparation and delivery

- [x] 7.1 Write `infra/deploy.sh` to record the current tag, write the environment file atomically, pull images, run migrations in a one-off container, recreate services, poll `/readyz`, and roll back to the recorded tag on failure; verify the script is idempotent when run twice against the same tag.
- [x] 7.2 Write `infra/host-bootstrap.sh` to create the deployment directory, Docker network, and environment file only when absent; verify a second run preserves an existing environment file and volume.
- [ ] 7.3 Add the production Caddy configuration with automatic TLS for the configured domain; verify HTTPS succeeds and the certificate is issued without operator action.
- [x] 7.4 Add the manual rollback command backed by the recorded previous tag; verify it restores the prior release without rebuilding an image.
- [ ] 7.5 Create the `deploy` workflow that builds and publishes both images to GHCR with commit-SHA tags, serializes deployments with a concurrency group, and invokes `infra/deploy.sh` over SSH with a pinned host key; verify two rapid dispatches run one after the other and the host ends on the newer tag.
- [ ] 7.6 Configure the protected GitHub Environment with host, user, SSH key, registry token, and runtime secrets; verify a deployment can pull a private image and that a missing secret fails the job before touching the host.
- [ ] 7.7 Verify migration failure handling by dispatching a release with a deliberately broken migration; confirm the deployment aborts and the previous containers keep serving.
- [x] 7.8 Document the deployment runbook, secret rotation, and rollback drill in `docs/deployment.md`; verify an operator can execute the rollback command as written.

## 8. Branch governance and release gate

- [ ] 8.1 Add the branch-name check that rejects pull requests whose head branch does not match `feature/<change-name>`; verify a pull request from a non-matching branch is blocked.
- [ ] 8.2 Write `infra/github/ruleset.sh` using `gh api` to require pull requests, required checks, linear history, squash merges, and branch deletion, with no contributor bypass; verify a direct push to `main` is rejected for a regular contributor and an administrator.
- [ ] 8.3 Create the `archive` label and add the gate workflow listening to both `pull_request: labeled` and `workflow_run: completed`, evaluating label, required-check, and mergeability predicates before merging; verify a pull request with green checks but no label does not merge.
- [ ] 8.4 Wire the gate to squash merge, delete the branch, and dispatch the deploy workflow with the merge commit SHA; verify a deploy run exists for the merge commit after a labeled merge.
- [ ] 8.5 Add single-pull-request reuse and archive idempotency to the archive guidance; verify a second workflow run on the same branch reuses the open pull request and skips re-archiving.
- [x] 8.6 Add the artifact `rules` and `operations.archive` blocks to `openspec/config.yaml`; verify `openspec instructions proposal --json` returns the rollback-plan rule and `openspec validate --specs --strict` still passes.
- [x] 8.7 Document the change-to-merge workflow in `docs/workflow.md`, including the archive label as the sole merge authorization; verify the steps match the gate workflow and the ruleset script.

## 9. Integration verification

- [ ] 9.1 Rehearse the full path on a disposable pull request: checks run, label applied, squash merge, deploy dispatched, both services healthy; verify the merge commit's images are the ones running.
- [ ] 9.2 Force a post-deploy health failure and verify automatic rollback restores the previous tag and reports the deployment as failed.
- [ ] 9.3 Run the manual rollback command on a healthy deployment and verify the prior release serves traffic within five minutes.
- [ ] 9.4 Verify the public port surface: HTTPS serves the frontend, the backend is unreachable from the internet, and PostgreSQL is reachable only from the container network.
- [x] 9.5 Reproduce from scratch: clone the repository, copy the environment example, run the quick start, and verify the local stack serves the index page.

## Workflow follow-up

- Run the archive on the feature branch, never on `main`.
- Run `openspec validate --specs --strict` before committing the archive.
- Push with `git push -u origin feature/bootstrap-project`.
- Open the pull request with `gh pr create --base main` only if one is not already open.
- Apply the `archive` label to authorize the squash merge; the label is the sole merge trigger.
