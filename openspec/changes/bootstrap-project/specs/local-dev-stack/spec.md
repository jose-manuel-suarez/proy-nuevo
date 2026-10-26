# Spec Delta

## Purpose

Provide a reproducible, containerized development environment in which both applications and PostgreSQL run together, and source edits take effect without rebuilding images.

## ADDED Requirements

### Requirement: Single-command startup
The development stack MUST start the database, backend, frontend, and edge proxy together with one documented command, and MUST NOT require a locally installed language runtime or database server.

#### Scenario: Full stack starts from a clean clone
- **WHEN** a developer clones the repository, copies the example environment file, and runs the documented start command
- **THEN** all four services reach a running state
- **AND** the frontend responds on the published local port

#### Scenario: Missing required configuration
- **WHEN** a required environment variable is absent
- **THEN** startup fails with an error that names the missing variable
- **AND** no service starts with a silent fallback value

### Requirement: Source hot reload
The stack MUST apply edits to backend and frontend source files without rebuilding images or recreating containers.

#### Scenario: Backend source edit
- **WHEN** a developer saves a change to a backend source file
- **THEN** the backend serves the changed behavior on the next request
- **AND** no image rebuild is required

#### Scenario: Template edit
- **WHEN** a developer saves a change to a Jinja2 template
- **THEN** the next page request renders the updated template

### Requirement: Dependency-aware readiness
Each service MUST report readiness only after its dependencies are reachable, and the stack MUST keep services alive while waiting for the database.

#### Scenario: Database starts last
- **WHEN** backend and frontend start before PostgreSQL accepts connections
- **THEN** they retry until the database is reachable
- **AND** they do not exit permanently during the wait

#### Scenario: Status inspection
- **WHEN** a developer inspects service status
- **THEN** each service reports healthy only after its dependencies respond

### Requirement: Environment-based configuration
All runtime configuration MUST come from environment variables, and the repository MUST document every required variable with a non-secret placeholder.

#### Scenario: Example file completeness
- **WHEN** a developer compares the example environment file with the variables the stack reads
- **THEN** every required variable appears with a placeholder value
- **AND** no real credential is committed to the repository

### Requirement: Persistent local database
The local database MUST retain its data across container restarts, and the stack MUST provide a documented reset that returns it to an empty initialized state.

#### Scenario: Restart preserves data
- **WHEN** the stack is stopped and started again without removing volumes
- **THEN** previously written rows are still present

#### Scenario: Documented reset
- **WHEN** a developer runs the documented reset command
- **THEN** the database is reinitialized empty

### Requirement: Limited local exposure
The stack MUST publish the edge proxy by default and MUST NOT publish the database port; applications MAY publish their own ports for direct debugging.

#### Scenario: Default port surface
- **WHEN** the stack starts with the documented default configuration
- **THEN** the frontend is reachable through the published proxy port
- **AND** PostgreSQL is reachable only from the container network unless a debugging override is explicitly enabled
