#!/usr/bin/env bash
# Deploy a released image tag to the host and verify it before declaring success.
#
# Required (from the environment or from $DEPLOY_DIR/.env):
#   IMAGE_TAG    release tag to deploy, e.g. sha-<commit>
#   GHCR_OWNER   registry owner/organization
#   GHCR_REPO    repository name
#   DOMAIN       public hostname served by Caddy
#
# Optional:
#   DEPLOY_DIR          deployment directory (default /opt/proy-nuevo)
#   HEALTHCHECK_URL     readiness URL (default https://$DOMAIN/readyz)
#   HEALTHCHECK_ATTEMPTS/HEALTHCHECK_INTERVAL  readiness polling knobs
#   GHCR_TOKEN          registry token for private packages
#
# Values passed by the caller take precedence over the environment file, so a
# rollback can select a tag without rewriting .env.
set -euo pipefail

requested_tag="${IMAGE_TAG:-}"
requested_owner="${GHCR_OWNER:-}"
requested_repo="${GHCR_REPO:-}"
requested_domain="${DOMAIN:-}"
requested_token="${GHCR_TOKEN:-}"

DEPLOY_DIR="${DEPLOY_DIR:-/opt/proy-nuevo}"

cd "$DEPLOY_DIR"

if [[ -f .env.incoming ]]; then
    install -m 600 .env.incoming .env.tmp
    mv .env.tmp .env
    rm -f .env.incoming
fi

if [[ ! -f .env ]]; then
    echo "missing $DEPLOY_DIR/.env; run host-bootstrap.sh first" >&2
    exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

# Caller-provided release identity wins over whatever the environment file says.
export IMAGE_TAG="${requested_tag:-${IMAGE_TAG:-}}"
export GHCR_OWNER="${requested_owner:-${GHCR_OWNER:-}}"
export GHCR_REPO="${requested_repo:-${GHCR_REPO:-}}"
export DOMAIN="${requested_domain:-${DOMAIN:-}}"

: "${IMAGE_TAG:?IMAGE_TAG is required}"
: "${GHCR_OWNER:?GHCR_OWNER is required}"
: "${GHCR_REPO:?GHCR_REPO is required}"
: "${DOMAIN:?DOMAIN is required}"

HEALTHCHECK_URL="${HEALTHCHECK_URL:-https://${DOMAIN}/readyz}"
HEALTHCHECK_ATTEMPTS="${HEALTHCHECK_ATTEMPTS:-60}"
HEALTHCHECK_INTERVAL="${HEALTHCHECK_INTERVAL:-2}"

if [[ -n "$requested_token" ]]; then
    printf '%s' "$requested_token" | docker login ghcr.io --username "$GHCR_OWNER" --password-stdin
fi

# The tag that is currently serving. It only becomes a rollback target after
# the new release proves healthy, so a failed attempt cannot erase history.
previous_tag=""
if [[ -f .current_tag ]]; then
    previous_tag="$(cat .current_tag)"
fi

compose=(docker compose -f compose.yaml -f compose.prod.yaml)

echo "pulling images for $IMAGE_TAG"
"${compose[@]}" pull

# Migrations run in a one-off container before any application container is
# replaced. A failing migration aborts here and leaves the old release serving.
echo "applying migrations for $IMAGE_TAG"
"${compose[@]}" run --rm --no-deps backend alembic upgrade head

echo "starting services for $IMAGE_TAG"
"${compose[@]}" up -d --remove-orphans

health_check() {
    local _
    for _ in $(seq 1 "$HEALTHCHECK_ATTEMPTS"); do
        if curl --fail --silent --show-error "$HEALTHCHECK_URL" >/dev/null; then
            return 0
        fi
        sleep "$HEALTHCHECK_INTERVAL"
    done
    return 1
}

if ! health_check; then
    echo "deployment of $IMAGE_TAG failed its health check" >&2
    if [[ -n "$previous_tag" && "$previous_tag" != "$IMAGE_TAG" ]]; then
        echo "rolling back to $previous_tag" >&2
        IMAGE_TAG="$previous_tag" "${compose[@]}" up -d --remove-orphans
        printf '%s\n' "$previous_tag" >.current_tag
    fi
    exit 1
fi

if [[ -n "$previous_tag" && "$previous_tag" != "$IMAGE_TAG" ]]; then
    printf '%s\n' "$previous_tag" >.previous_tag
fi
printf '%s\n' "$IMAGE_TAG" >.current_tag
echo "deployed $IMAGE_TAG"
