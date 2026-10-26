#!/usr/bin/env bash
# Redeploy the previously recorded release without rebuilding any image.
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/proy-nuevo}"
cd "$DEPLOY_DIR"

if [[ ! -f .previous_tag ]]; then
    echo "no .previous_tag recorded in $DEPLOY_DIR" >&2
    exit 1
fi

tag="$(cat .previous_tag)"
if [[ -z "$tag" ]]; then
    echo ".previous_tag is empty" >&2
    exit 1
fi

echo "rolling back to $tag"
# deploy.sh reads the rest of the release identity from .env and records the
# faulty release as the new rollback target once the old tag is healthy.
DEPLOY_DIR="$DEPLOY_DIR" IMAGE_TAG="$tag" ./infra/deploy.sh
