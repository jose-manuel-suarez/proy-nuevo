# Spec Delta

## Purpose

Turn every merge to the main branch into a verified deployment on the host, and guarantee a tested path back to the previous release.

## ADDED Requirements

### Requirement: Release on merge
Every merge to the main branch MUST produce published images tagged with the merge commit, and the pipeline MUST NOT publish a release from an unmerged commit or from a failing integration run.

#### Scenario: Merge publishes a release
- **WHEN** a pull request is merged into main
- **THEN** both images are published with tags derived from the merge commit

#### Scenario: Failing integration run
- **WHEN** integration checks fail for a commit
- **THEN** no release image is published for that commit

### Requirement: Serialized deployment
The pipeline MUST NOT run two deployments concurrently, and the host MUST end in the state of the most recent successfully deployed release.

#### Scenario: Overlapping merges
- **WHEN** a second merge arrives while a deployment is in progress
- **THEN** deployments run one at a time
- **AND** the host ends on the newer release

### Requirement: Migrations before rollout
The pipeline MUST apply pending migrations as a discrete step before new application containers serve traffic, and MUST NOT run migrations automatically during application startup.

#### Scenario: Successful migration
- **WHEN** a release contains pending migrations
- **THEN** migrations run before the new application containers start
- **AND** the application starts only after migrations succeed

#### Scenario: Failed migration
- **WHEN** a migration fails
- **THEN** the deployment aborts
- **AND** the previously running application containers keep serving

### Requirement: Schema compatibility across releases
Every schema change MUST remain compatible with the immediately previous application release, so that rollback does not require reversing the schema.

#### Scenario: Destructive change
- **WHEN** a release removes or renames a column or table still used by the previous release
- **THEN** the change is split across releases following an expand and contract sequence

### Requirement: Available edge during rollout
The edge proxy MUST continue serving throughout a deployment and MUST route traffic only to containers that report ready.

#### Scenario: Traffic during replacement
- **WHEN** application containers are replaced during a deployment
- **THEN** requests through the proxy continue to be served
- **AND** the proxy stops routing to a container that reports unhealthy

### Requirement: Health verification and automatic rollback
The pipeline MUST verify the health of both applications after deployment, and MUST restore the previous release automatically when verification fails.

#### Scenario: Failed post-deploy check
- **WHEN** a deployed application fails its health check after the rollout
- **THEN** the pipeline redeploys the previous release
- **AND** the deployment is reported as failed

#### Scenario: Successful verification
- **WHEN** both applications report healthy after the rollout
- **THEN** the deployment is reported as successful
- **AND** the deployed tag becomes the recorded previous release for the next deployment

### Requirement: Manual rollback
The host MUST record the currently running release, and a documented command MUST restore the previous recorded release without rebuilding images.

#### Scenario: Operator-initiated rollback
- **WHEN** an operator runs the documented rollback command
- **THEN** the previously recorded release is redeployed
- **AND** the operation completes without a new image build

### Requirement: Runtime secrets
Secrets MUST be supplied to containers at runtime from the host environment and MUST NOT be embedded in images, repository files, or pipeline logs.

#### Scenario: Secret rotation
- **WHEN** a credential is rotated on the host
- **THEN** the affected service picks it up after a restart
- **AND** no image is rebuilt

### Requirement: Idempotent host bootstrap
The pipeline MUST be able to prepare an empty host, and repeated preparation MUST NOT overwrite existing data volumes or environment files.

#### Scenario: First deployment
- **WHEN** the pipeline targets a host that has no deployment directory
- **THEN** it creates the required directories, network, and environment file
- **AND** the release is deployed

#### Scenario: Repeated preparation
- **WHEN** the pipeline prepares a host that is already configured
- **THEN** existing data volumes and environment files are preserved

### Requirement: Automatic TLS
The edge proxy MUST serve the configured domain over HTTPS using certificates provisioned and renewed without manual intervention.

#### Scenario: Certificate lifecycle
- **WHEN** the stack starts with a public domain pointed at the host
- **THEN** HTTPS requests succeed with a valid certificate
- **AND** renewal happens without an operator action
