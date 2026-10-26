#!/usr/bin/env bash
# Apply the main-branch ruleset and merge settings. Idempotent: re-running
# updates the existing ruleset instead of creating a duplicate.
#
# Requirements: gh CLI authenticated with repository administration rights.
set -euo pipefail

REPO="${REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
RULESET_NAME="main-protection"

payload="$(mktemp)"
trap 'rm -f "$payload"' EXIT

cat >"$payload" <<'JSON'
{
  "name": "main-protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          { "context": "branch-name" },
          { "context": "lint" },
          { "context": "typecheck" },
          { "context": "backend-tests" },
          { "context": "frontend-tests" },
          { "context": "migrations" },
          { "context": "images (backend)" },
          { "context": "images (frontend)" }
        ]
      }
    },
    { "type": "non_fast_forward" },
    { "type": "deletion" },
    { "type": "required_linear_history" }
  ],
  "bypass_actors": []
}
JSON

existing_id="$(gh api "repos/$REPO/rulesets" --jq ".[] | select(.name == \"$RULESET_NAME\") | .id" | head -n 1)"

if [[ -n "$existing_id" ]]; then
    echo "updating ruleset $RULESET_NAME ($existing_id) on $REPO"
    gh api -X PUT "repos/$REPO/rulesets/$existing_id" --input "$payload" >/dev/null
else
    echo "creating ruleset $RULESET_NAME on $REPO"
    gh api -X POST "repos/$REPO/rulesets" --input "$payload" >/dev/null
fi

echo "enforcing squash merges and branch deletion on $REPO"
gh api -X PATCH "repos/$REPO" \
    -F allow_squash_merge=true \
    -F allow_merge_commit=false \
    -F allow_rebase_merge=false \
    -F delete_branch_on_merge=true >/dev/null

if gh label list --repo "$REPO" --search archive --json name --jq '.[].name' | grep -qx archive; then
    echo "label archive already exists"
else
    gh label create archive --repo "$REPO" \
        --color 0e8a16 \
        --description "Authorizes the squash merge and deployment"
fi

echo "done"
