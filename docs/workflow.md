# Change workflow

Every change follows the same path: a feature branch, a pull request, required
checks, and a label that authorizes the squash merge. Nothing reaches `main`
any other way.

## Branches

```
main
  |
  +-- feature/<change-name>     one branch per OpenSpec change
```

Branch names must match `^feature/[a-z0-9]+(-[a-z0-9]+)*$`. The `branch-name`
CI job enforces it, and that check is required by the ruleset. Use the same
name as the OpenSpec change: change `add-user-auth` lives on
`feature/add-user-auth`.

## Lifecycle

```bash
# 1. create the change and implement it
openspec new change "add-user-auth"
git checkout -b feature/add-user-auth

# 2. archive on the feature branch, never on main
openspec archive "add-user-auth" --yes
openspec validate --specs --strict

# 3. commit and push
git add -A
git commit -m "feat: add user auth"
git push -u origin feature/add-user-auth

# 4. open the pull request once
gh pr create --base main --fill

# 5. after required checks are green, a maintainer applies the label
gh pr edit --add-label archive
```

The gate workflow then squash-merges the pull request, deletes the branch, and
dispatches the deployment with the merge commit.

## Why the label

The `archive` label is the only merge authorization. It is applied by a human
after review, and it means "this change is complete, archived, and verified".
Approval or green checks alone never merge.

```text
 label applied ──┐
                 ├──> gate evaluates ──> label? checks? mergeable? ──> merge ──> deploy
 CI completed ───┘
```

The gate listens to both `pull_request: labeled` and `workflow_run: completed`
because either can happen first. The predicate is identical, and merging is
idempotent, so a duplicate evaluation is harmless.

## Why deployment is dispatched explicitly

GitHub does not start new workflow runs for events caused by the repository's
`GITHUB_TOKEN`, with the exception of `workflow_dispatch` and
`repository_dispatch`. A merge performed by the gate therefore would not
trigger an `on: push` deploy workflow. The gate calls `gh workflow run deploy.yml`
with the merge commit instead. Do not replace this with a push trigger unless
the merge switches to a GitHub App token.

## Protection rules

`infra/github/ruleset.sh` applies, on `main`:

- pull request required, with no bypass actors (administrators included);
- required checks: `branch-name`, `lint`, `typecheck`, `backend-tests`,
  `frontend-tests`, `migrations`, `images (backend)`, `images (frontend)`;
- branches must be up to date before merging;
- linear history, no force pushes, no deletion;
- squash-only merges and automatic branch deletion.

```bash
gh auth login
./infra/github/ruleset.sh
```

The script is idempotent and must be re-run after adding or renaming a required
CI job.

### Bootstrap order

On a brand-new repository, the ruleset cannot require checks that have never
run on `main`. The bootstrap change is merged first by repository
administration, then the ruleset is applied. From that point on, every change
uses the label gate. Do not apply the ruleset before the CI workflow exists on
`main`, or the first pull request will wait forever for checks that are not
registered.

## Merge behavior

- Squash only; `main` stays linear.
- The source branch is deleted by the merge.
- A pull request with green checks but no `archive` label stays open.
- A pull request already merged is not merged again; the gate exits quietly.
