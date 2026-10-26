# Spec Delta

## Purpose

Produce self-contained, production-grade container images for both applications that run unprivileged, report their health, and carry immutable version identifiers.

## ADDED Requirements

### Requirement: Self-contained runtime
Each application image MUST contain its code and runtime dependencies, and MUST NOT depend on host-mounted source, a host-installed language runtime, or a build performed outside the image.

#### Scenario: Run without mounts
- **WHEN** an image is started on a host that has no language runtime installed and no source directory mounted
- **THEN** the application starts and serves requests

### Requirement: Minimal runtime contents
The runtime image MUST NOT include test runners, linters, compilers, or package-manager build tooling.

#### Scenario: Development tooling absent
- **WHEN** the runtime image is inspected for development executables
- **THEN** test and lint commands are not present
- **AND** the application still starts normally

### Requirement: Unprivileged execution
Every application image MUST run its process as a non-root user with a fixed identity.

#### Scenario: Process identity
- **WHEN** the application process is inspected inside a running container
- **THEN** its user identifier is not zero
- **AND** it cannot write to the image's system directories

### Requirement: Health declaration
Each image MUST declare a health check that probes the application's health endpoint and reports unhealthy when the probe fails.

#### Scenario: Healthy application
- **WHEN** the application and its dependencies are available
- **THEN** the container reports healthy within the configured interval

#### Scenario: Failed dependency
- **WHEN** a required dependency stops responding
- **THEN** the health probe fails and the container reports unhealthy

### Requirement: Deterministic dependency installation
Image builds MUST install application dependencies from a committed lockfile and MUST NOT resolve unversioned dependencies during the build.

#### Scenario: Lockfile governs versions
- **WHEN** the lockfile is unchanged and an image is rebuilt
- **THEN** the installed dependency versions match the previous build

### Requirement: Immutable image tags
Every published image MUST carry a tag derived from the source commit, and deployment MUST reference that immutable tag rather than a mutable alias.

#### Scenario: Tag identifies the source
- **WHEN** two different commits are built
- **THEN** their published images have distinct tags
- **AND** the deployment configuration references the commit-derived tag

### Requirement: Graceful termination
Both images MUST handle termination signals by stopping acceptance of new work and exiting within the orchestrator's grace period.

#### Scenario: Container stop during traffic
- **WHEN** the container receives a termination signal while serving a request
- **THEN** it finishes or rejects the in-flight request cleanly
- **AND** the process exits with a success status inside the grace period

### Requirement: No embedded secrets
Images MUST NOT contain secret values, and every secret MUST be supplied at runtime.

#### Scenario: Image inspection reveals no credentials
- **WHEN** an image's filesystem and environment metadata are inspected
- **THEN** no credential, token, or private key is present
- **AND** rotating a secret requires no image rebuild
