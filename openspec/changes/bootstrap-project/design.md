# Design

## Context

The repository has no application code, no containers, and no pipeline. The target is a single VPS running Docker Compose, with GitHub as the source of truth and GitHub Actions as the automation surface. Development happens on Windows, so bind-mount behavior and reload semantics must be chosen with that in mind. There is no authentication, no user data, and no traffic yet, which makes this the cheapest moment to fix boundaries.

The specification defines behavior; this document records how the system will be built and why the alternatives were rejected. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**

- A local stack that starts with one command and behaves the same way on every machine.
- Two independently buildable images with the same operational contract (health, signals, non-root).
- A pull request that cannot merge while broken, and cannot merge without an explicit human release signal.
- A deployment path that is reproducible by hand, not only inside a workflow, so recovery never depends on CI being available.
- A rollback that works with the previous image and the new schema.

**Non-Goals:**

- Horizontal scaling, multiple hosts, or an orchestrator beyond Compose.
- A staging environment; the `archive` label already provides the human gate.
- User authentication, sessions, or authorization.
- A public API surface; the backend is reachable only from the frontend container.
- Log aggregation, metrics, tracing, and alerting beyond process logs and health checks.
- Automated database backups. The residual risk is recorded below and belongs to a later change.
- A JavaScript build pipeline; HTMX is served as a vendored static asset.

## Decisions

### D1: Monorepo with two deployable applications

`backend/` and `frontend/` are separate applications with separate images and separate test suites, but they live in one repository alongside `infra/`.

**Why:** a change routinely touches an endpoint, the template that calls it, and the Compose service that runs it. One branch, one pull request, one atomic revert. The `feature/<change-name>` rule and the OpenSpec change model both assume this.

**Alternatives:** two repositories would force coordinated pull requests and make a cross-cutting rollback manual; submodules add tooling without removing the coordination cost.

### D2: The browser talks only to the frontend

The edge proxy routes public traffic to Flask. Flask calls FastAPI over the Compose network with a shared service token header. The browser never reaches FastAPI directly.

**Why:** server-side rendering plus HTMX means every interaction already goes through Flask. Keeping the API internal removes CORS, removes token handling from the browser, and leaves one public surface to harden. The service token gives defense in depth without a full auth system.

**Alternatives:** direct browser-to-API calls would need CORS policy, a public API contract, and browser-side credential handling — all premature before a real authentication design exists.

### D3: Caddy as the edge proxy

Caddy terminates TLS, obtains and renews certificates automatically, and proxies to Flask.

**Why:** six lines of configuration versus a certbot timer and renewal hooks. On a single host, fewer moving parts wins.

**Alternatives:** nginx needs certificate lifecycle management; Traefik is excellent at label-driven dynamic routing but that capability is unused with one upstream.

### D4: Layered Compose files

`compose.yaml` holds the shared service graph, `compose.dev.yaml` adds bind mounts, reload commands, and debug ports, and the production invocation adds `compose.prod.yaml` with image references and no source mounts.

**Why:** one service graph, environment-specific overrides, and a visible diff between environments. Copy-pasting two full Compose files guarantees drift.

**Alternatives:** fully separate files per environment; a single file with many conditionals. Both make the environment difference invisible in review.

### D5: Async SQLAlchemy 2 with asyncpg

The backend uses the async SQLAlchemy 2 API with `asyncpg`, and Alembic uses its async template.

**Why:** FastAPI is async-native, and a synchronous driver inside async routes blocks the event loop under load. Raw SQLAlchemy 2 keeps the query layer explicit. The frontend never touches the database, so there is exactly one access path to keep consistent.

**Alternatives:** synchronous SQLAlchemy with `psycopg` is simpler to debug but invites blocking calls; SQLModel trades control for brevity and lags SQLAlchemy releases.

### D6: uv for dependency and lock management

Both Python applications are managed with `uv`, with a committed lockfile and a pinned Python 3.12 base image.

**Why:** one tool for resolution, locking, and install; fast enough for CI; the lockfile is the contract the image build consumes.

**Alternatives:** pip-tools requires two files and two commands; Poetry adds a second resolver and historically slow installs. Python 3.13 is deliberately deferred until the pinned dependency set is proven.

### D7: Test strategy split by boundary

Backend tests run pytest against a real PostgreSQL database created for the run. Frontend tests run pytest with Flask's test client and a stubbed API transport. A separate smoke job starts the built Compose stack and asserts the rendered page.

**Why:** SQL dialect differences make SQLite a false friend; the frontend's contract with the API is HTTP-shaped, so a transport stub is the honest test double. The smoke job is the only place the two applications meet for real.

**Alternatives:** mocking the database in backend tests hides migration and SQL errors; running the whole stack for every unit test is slow and brittle.

### D8: Merge gate driven by CI completion and label events

The gate workflow listens to both `pull_request: labeled` and `workflow_run: completed`. On either event it evaluates the same predicate — label present, required checks green, pull request mergeable — and merges only when all hold.

**Why:** either event can arrive first. Label-then-CI and CI-then-label must both converge, and evaluating the predicate twice is harmless because merging is idempotent.

```
 label applied ----> gate evaluates ---+
                                      +--> predicate true --> squash merge --> dispatch deploy
 CI completed  ----> gate evaluates ---+
```

**Alternatives:** a `labeled`-only trigger deadlocks when checks finish later; native auto-merge obscures which identity performed the merge, which matters for the token-event rule below.

### D9: Explicit deploy dispatch after the merge

The gate merges with the repository token, then calls `gh workflow run deploy.yml` with the merge commit SHA.

**Why:** GitHub does not start new workflow runs for events caused by the default `GITHUB_TOKEN` — with the exceptions of `workflow_dispatch` and `repository_dispatch`. An `on: push` deploy workflow would never fire. Explicit dispatch is deterministic and passes the SHA directly instead of re-deriving it.

**Alternatives:** a GitHub App token makes the merge emit a real push event but adds key management; `workflow_run` chaining is fragile because the gate's own completion precedes the merge's side effects.

```
 GitHub Actions              VPS (deploy user)          Compose              Postgres
      |                             |                       |                    |
      | ssh deploy@host             |                       |                    |
      |---------------------------->|                       |                    |
      | record current tag          |                       |                    |
      | write env file (atomic)     |                       |                    |
      | docker compose pull         |                       |                    |
      |---------------------------->|---------------------->|                    |
      | migrate (one-off container) |                       |                    |
      |---------------------------->|---------------------->|------------------->|
      |                             |                       |  alembic upgrade   |
      | up -d with new tag          |                       |                    |
      |---------------------------->|---------------------->|                    |
      | poll readiness until green  |                       |                    |
      |---------------------------->|                       |                    |
      | 200 OK                      |                       |                    |
      |<----------------------------|                       |                    |
      | on failure: up -d with previous tag                 |                    |
      |---------------------------->|---------------------->|                    |
```

### D10: Migrations as a one-off step with expand/contract

The deploy script runs `alembic upgrade head` in a dedicated container before replacing application containers. Application startup never runs migrations. Migrations take a PostgreSQL advisory lock.

**Why:** running migrations on startup races when more than one container starts, and it hides failures until traffic is already flowing. Expand/contract keeps the previous image valid against the new schema, which is what makes the rollback in D9 real rather than aspirational.

**Alternatives:** an init container per service duplicates work; a manual migration step removes the automation guarantee that schema and code ship together.

### D11: Secrets flow from GitHub Environment to the host

Deployment credentials live in a protected GitHub Environment. The deploy job writes the runtime environment file atomically on the host, and the host preserves it when the pipeline cannot reach GitHub.

**Why:** one authoritative source, no secrets in the repository, and rotation is a workflow re-run rather than an SSH session. Pinning the host key prevents man-in-the-middle on the deploy path.

**Alternatives:** SOPS or Vault add a decryption step and new credentials to protect; committing an env file is rejected outright.

### D12: Branch ruleset defined once, as code in `infra/github/`

The ruleset is applied with `gh api` from a script kept under `infra/github/`, including required checks, squash-only merges, linear history, and deletion of merged branches. Contributor bypass is disabled.

**Why:** a screenshot of UI settings is not reviewable and drifts silently. A script is diffable and re-appliable.

**Alternatives:** Terraform is heavier than a two-hundred-line repository needs; manual UI configuration is the status quo this change exists to escape.

### D13: Health endpoints with distinct meanings

Both applications expose `/healthz` (process alive, no dependencies) and `/readyz` (dependencies verified; backend checks the database, frontend checks the backend). Container health checks use `/healthz`; deployment verification and proxy routing use `/readyz`.

**Why:** conflating the two produces restart storms during a database blip. Separating them lets the proxy stop routing while the orchestrator leaves the process alone.

### D14: No JavaScript toolchain

HTMX is vendored into the frontend's static assets. There is no Node build step, no bundler, and no CDN dependency.

**Why:** reproducibility and offline builds. A CDN reference would make the rendered page depend on a third party at runtime.

## Risks / Trade-offs

- **Single host is a single point of failure** → accepted for this stage. The volume persists containers, and the deploy path is reproducible by hand. Off-host backups are an explicit follow-up change, not silently assumed.
- **Merges performed by the repository token do not trigger push workflows** → deploy is dispatched explicitly with the SHA; the pipeline test asserts a deploy run exists after a labeled merge.
- **Expand/contract is a review discipline, not something CI can fully prove** → the proposal template requires a rollback plan and the review checklist calls out destructive migrations; a destructive change is split into two changes.
- **Brief edge disruption during container replacement** → services are replaced individually and only after health checks pass; Caddy retries upstream connections. A few seconds of degraded service is accepted rather than adding a second host.
- **Windows bind-mount reload can miss events** → backend and frontend reloaders use polling in the dev overlay, and the README recommends WSL2 for the fastest feedback loop.
- **Secret drift between GitHub and host** → the environment file is written from the workflow on every deploy; a stale hand-edited value is overwritten by design.
- **GHCR packages are private by default** → the host authenticates to the registry with a scoped token stored in the host environment file; package visibility is an open question until the first publish.
- **Auto-deploy to production on merge** → the `archive` label is the human authorization, health verification is automatic, and rollback is one command. The residual risk is a change that passes checks and is still wrong, which no pipeline removes.
- **CI runtime grows with a real PostgreSQL service and a smoke stack** → jobs run in parallel and dependency installation is cached by lockfile hash.

## Migration Plan

The change is additive and can be delivered in ordered phases, each independently verifiable:

1. **Scaffold** — repository layout, environment examples, README, baseline Alembic revision. Local stack starts; no external state.
2. **Quality gates** — CI workflow on pull requests. Merge remains manual until the ruleset is applied.
3. **Host preparation** — directories, network, environment file, Caddy configuration, deploy script. First deployment is triggered manually with a known SHA.
4. **Automation** — publish workflow, deploy workflow, merge gate, then the ruleset and label. Apply protection last so the pipeline can be observed before it becomes mandatory.
5. **Rehearsal** — a labeled pull request proves merge and deploy; a forced health failure proves automatic rollback; the manual rollback command is executed once.

**Rollback of this change:** revert the squashed commit on `main`. Images are immutable by SHA, so the previous deployment can be restored by redeploying the prior tag. No data migration needs reversing because the baseline schema is additive.

## Open Questions

- The production domain name and TLS contact address are not yet chosen; both are deployment inputs, not design constraints.
- The VPS provider and SSH access details are unknown; the deploy script parameters are provider-agnostic.
- GHCR package visibility (public versus private) can be decided at first publish without changing the pipeline.
