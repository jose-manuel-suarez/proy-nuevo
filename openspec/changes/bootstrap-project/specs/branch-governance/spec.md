# Spec Delta

## Purpose

Govern how work reaches the main branch: a feature branch per change, a reviewed pull request, passing checks, and a single label that authorizes the merge.

## ADDED Requirements

### Requirement: One feature branch per change
Every change MUST be developed on a branch named `feature/<change-name>`, and the main branch MUST NOT accept direct commits or pushes.

#### Scenario: Change workflow
- **WHEN** a developer starts work on a change
- **THEN** the work is committed to a branch matching `feature/<change-name>`

#### Scenario: Direct push attempt
- **WHEN** a user attempts to push a commit directly to main
- **THEN** the push is rejected

#### Scenario: Unexpected branch name
- **WHEN** a pull request originates from a branch that does not match the naming convention
- **THEN** the merge remains blocked until the branch is renamed

### Requirement: Pull request required
Every update to main MUST arrive through a pull request, and the protection rules MUST apply to administrators as well as regular contributors.

#### Scenario: Administrator bypass attempt
- **WHEN** a repository administrator attempts a direct update to main that bypasses a pull request
- **THEN** the update is rejected

### Requirement: Passing checks required
A pull request MUST NOT merge while any required integration check is failing, pending, or missing.

#### Scenario: Green checks
- **WHEN** all required checks have passed and the label condition is met
- **THEN** the pull request becomes mergeable

#### Scenario: Red checks
- **WHEN** a required check fails
- **THEN** the merge is blocked even if the label is present

### Requirement: Archive label as sole merge authorization
A pull request MUST merge only after the `archive` label is applied, and green checks or human approval alone MUST NOT authorize a merge.

#### Scenario: Approved but unlabeled
- **WHEN** a pull request is approved and all checks pass but the `archive` label is absent
- **THEN** no merge occurs

#### Scenario: Label applied
- **WHEN** the `archive` label is applied to a pull request with passing checks
- **THEN** the pull request is merged automatically

### Requirement: Squash merge and branch cleanup
Merges into main MUST be squash merges, and the source branch MUST be deleted after the merge.

#### Scenario: Merge result
- **WHEN** a pull request is merged
- **THEN** main receives a single squashed commit
- **AND** the feature branch is deleted

### Requirement: Archive before the pull request
A completed change MUST be archived on its feature branch, never on main, and its specs MUST pass strict validation before the archive commit is pushed. A change that is already archived MUST NOT be archived again.

#### Scenario: Standard archive
- **WHEN** a developer finishes the implementation tasks
- **THEN** the archive runs on the feature branch
- **AND** strict spec validation passes before the commit is pushed

#### Scenario: Repeated archive attempt
- **WHEN** the archive already ran on the branch and the command is attempted again
- **THEN** the step is skipped
- **AND** validation and pull request handling continue

### Requirement: Single pull request per branch
The workflow MUST NOT open a second pull request for a branch that already has an open one.

#### Scenario: Existing pull request
- **WHEN** a branch already has an open pull request
- **THEN** subsequent workflow runs reuse it instead of creating another

### Requirement: Dedicated merge identity
Automated merging MUST use a dedicated identity limited to the permissions the merge requires, and MUST NOT use a personal administrator credential.

#### Scenario: Automation credentials
- **WHEN** the merge automation authenticates
- **THEN** it uses a token scoped to repository contents and pull requests
- **AND** the automation cannot alter branch protection rules
