#!/usr/bin/env bash
# Reset only the local PostgreSQL volume and bring the development stack back.
set -euo pipefail

cd "$(dirname "$0")/.."

compose=(docker compose -f compose.yaml -f compose.dev.yaml)

"${compose[@]}" down

if docker volume inspect proy-nuevo_postgres_data >/dev/null 2>&1; then
    docker volume rm proy-nuevo_postgres_data
fi

"${compose[@]}" up -d --wait
