#!/usr/bin/env bash
# Prepare a host for the first deployment. Safe to run repeatedly: it never
# overwrites an existing environment file, deployment directory, or volume.
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/proy-nuevo}"

# Compose derives the project name from the deployment directory unless
# COMPOSE_PROJECT_NAME overrides it. The network must carry Compose's labels,
# otherwise `docker compose up` refuses a network it did not create itself.
PROJECT="${COMPOSE_PROJECT_NAME:-$(basename "$DEPLOY_DIR" | tr '[:upper:]' '[:lower:]')}"
NETWORK="${NETWORK:-${PROJECT}_internal}"

mkdir -p "$DEPLOY_DIR/infra/caddy" "$DEPLOY_DIR/infra/github"

if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
    docker network create \
        --label "com.docker.compose.project=$PROJECT" \
        --label "com.docker.compose.network=internal" \
        "$NETWORK" >/dev/null
    echo "created network $NETWORK"
else
    echo "network $NETWORK already exists"
fi

if [[ -f "$DEPLOY_DIR/.env" ]]; then
    echo "environment file already exists; leaving it untouched"
elif [[ -f "$DEPLOY_DIR/.env.incoming" ]]; then
    install -m 600 "$DEPLOY_DIR/.env.incoming" "$DEPLOY_DIR/.env"
    rm -f "$DEPLOY_DIR/.env.incoming"
    echo "installed environment file from .env.incoming"
elif [[ -f "$DEPLOY_DIR/.env.example" ]]; then
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
    chmod 600 "$DEPLOY_DIR/.env"
    echo "installed environment file from .env.example; review it before deploying"
else
    echo "no environment file available; copy .env.example to $DEPLOY_DIR/.env" >&2
    exit 1
fi

for required in compose.yaml compose.prod.yaml infra/deploy.sh infra/caddy/Caddyfile.prod; do
    if [[ ! -f "$DEPLOY_DIR/$required" ]]; then
        echo "missing $DEPLOY_DIR/$required; copy the release files first" >&2
        exit 1
    fi
done

echo "host ready at $DEPLOY_DIR"
