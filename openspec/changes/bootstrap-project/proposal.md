# Proposal

## Why

The workspace is empty: no source code, no containers, no pipeline, and no specs. Any project started here without a fixed baseline will accumulate hand-built environments, undocumented deploy steps, and quality gates that exist only in someone's memory. This change establishes a reproducible, container-first baseline with automated integration and continuous delivery so that every later change lands on rails instead of on improvisation.

## What Changes

- Introduce a monorepo layout with two separately deployable applications: `backend/` (FastAPI, Pydantic v2, SQLAlchemy 2, Alembic) and `frontend/` (Flask 3, Jinja2, HTMX, server-side rendering), plus `infra/` for deployment assets.
- Add a containerized local development stack where every service, including PostgreSQL, runs in Docker with bind-mounted code and hot reload.
- Add multi-stage production images for both applications, running as non-root with health checks, and a single edge proxy that terminates TLS.
- Add a GitHub Actions integration pipeline: linting, type checking, backend and frontend tests against a real PostgreSQL service, and image builds.
- Add a continuous delivery pipeline that publishes images to GitHub Container Registry, applies Alembic migrations, deploys to a single VPS with Docker Compose over SSH, verifies health, and supports rollback to the previous image tag.
- Add branch governance: `main` accepts no direct pushes, every change lands through a `feature/<change-name>` branch and pull request, and a pull request merges only when the `archive` label is applied.
- Record the project's artifact rules and archive guidance in `openspec/config.yaml` so every subsequent change follows the same conventions.
- Defer authentication, staging environments, and public API exposure; the browser talks only to the frontend, and the backend stays on the internal container network.

## Capabilities

### New Capabilities

- `local-dev-stack`: the containerized developer environment — Compose topology, bind-mounted source, hot reload, environment configuration, and database readiness.
- `container-images`: production-grade images for backend and frontend — multi-stage builds, non-root execution, health endpoints, and image tagging.
- `ci-pipeline`: automated verification on every pull request — lint, type check, tests against PostgreSQL, image build, and required status checks.
- `cd-pipeline`: automated release to the VPS — registry publication, migration execution, deployment, health verification, and rollback.
- `branch-governance`: the Git and GitHub rules that govern how work reaches `main` — branch naming, protection ruleset, and the label-triggered squash merge.

### Modified Capabilities

None. The project has no existing specs; this change introduces the initial capability set.

## Impact

- New repository structure: `backend/`, `frontend/`, `infra/`, root Compose files, `.env.example`, `.dockerignore`, `.gitignore`, `README.md`.
- New dependencies: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, asyncpg, Flask 3, Jinja2, HTMX (static asset), pytest, ruff, plus test and build tooling.
- New external dependencies: GitHub repository with Actions and Container Registry, a VPS reachable over SSH with Docker and Compose installed, and a domain name for TLS.
- New GitHub configuration: ruleset on `main`, required status checks, repository secrets for SSH deployment and environment configuration, and the `archive` label.
- No existing code, data, or production traffic is affected; the system does not yet serve users.

## Rollback Plan

This change is additive: it creates new files and new GitHub configuration, with no existing code or data to migrate.

- **Before first deploy:** revert the merge commit or close the pull request. Nothing external has been provisioned, and no images have been published beyond build artifacts.
- **After images are published but before the VPS is configured:** delete the GHCR packages and disable the workflows. The repository remains usable for development.
- **After a successful deploy:** roll back by redeploying the previous image tag recorded on the VPS; if the release itself is faulty, revert the merge commit on `main` through a normal pull request, which republishes the prior commit's images. Migrations follow an expand/contract pattern, so reverting an application image does not require reverting the schema.
- **Workflow or ruleset misconfiguration:** disable the affected workflow or remove the ruleset through the GitHub UI. Branch protection is the only guardrail involved and can be restored without touching application state.
- **Data risk:** the only persistent state is the PostgreSQL volume, created empty by this change. There is no user data to restore during the bootstrap window.
