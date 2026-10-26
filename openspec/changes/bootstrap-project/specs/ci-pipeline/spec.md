# Spec Delta

## Purpose

Verify every proposed change automatically, using quality gates that block merging when behavior, types, migrations, or images are broken.

## ADDED Requirements

### Requirement: Coverage of proposed changes
The integration pipeline MUST run for every pull request targeting the main branch and for every push to a change branch.

#### Scenario: Pull request opened
- **WHEN** a pull request targeting main is opened or updated
- **THEN** the pipeline starts automatically
- **AND** its results are attached to the pull request

#### Scenario: Direct branch push
- **WHEN** a commit is pushed to a change branch
- **THEN** the pipeline runs against that commit

### Requirement: Static analysis gates
The pipeline MUST run linting and static type analysis, and MUST fail when either reports a violation.

#### Scenario: Lint violation
- **WHEN** a change introduces a lint violation
- **THEN** the lint job fails
- **AND** the pull request cannot merge

#### Scenario: Type error
- **WHEN** a change introduces a type error
- **THEN** the type-check job fails
- **AND** the pull request cannot merge

### Requirement: Backend tests on PostgreSQL
The pipeline MUST execute the backend test suite against a real PostgreSQL instance, and MUST NOT substitute an in-memory or SQLite database.

#### Scenario: Backend suite runs
- **WHEN** the backend test job executes
- **THEN** it connects to a PostgreSQL instance created for that run
- **AND** failures are reported individually

#### Scenario: Test isolation
- **WHEN** the backend suite writes data
- **THEN** it does so in a database dedicated to the run
- **AND** no development or production data is touched

### Requirement: Frontend tests
The pipeline MUST execute the frontend test suite, including rendering of the server-side templates it serves.

#### Scenario: Template regression
- **WHEN** a change breaks a template used by a tested page
- **THEN** the frontend test job fails

### Requirement: Migration consistency
The pipeline MUST verify that migrations apply cleanly to an empty database and that the data model produces no pending migration.

#### Scenario: Migration applies from empty
- **WHEN** the migration check runs against an empty database
- **THEN** every migration applies successfully

#### Scenario: Model drift
- **WHEN** the data model differs from the migrated schema
- **THEN** the migration check fails and reports a pending change

### Requirement: Image build verification
The pipeline MUST build both application images on every pull request and MUST NOT publish them from a pull request.

#### Scenario: Broken image definition
- **WHEN** a change breaks a Dockerfile or its build context
- **THEN** the image build job fails
- **AND** no image is published

#### Scenario: Successful pull request build
- **WHEN** all checks pass on a pull request
- **THEN** both images build successfully
- **AND** the registry receives no release tags from that run
