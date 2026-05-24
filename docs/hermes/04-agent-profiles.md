# Agent Profiles

Hermes bot profiling is agent identity architecture, not static prompting.

Each bot has a structured profile. The runtime prompt is generated from the profile and current workflow context.

## Profile Shape

```text
AgentProfile
  id
  name
  type
  scope
  role_contract
  responsibilities
  non_responsibilities
  permissions
  allowed_tools
  denied_tools
  memory_sources
  learning_rules
  confidence_rubric
  escalation_rules
  review_rules
  communication_style
  model_config
  version
```

Runtime context is generated from:

```text
agent profile
workflow state
ticket/project context
relevant memory
available tools
current constraints
```

## Storage

Profiles should use two layers:

```text
Versioned manifests
  Stable identity, role contracts, permissions, rubrics, learning rules.

Database records
  Active profile version, runtime state, project assignments, learned memory
  links, performance history, approved overrides.
```

## Core Profiles

### Hermes-Triage

Normalizes requests, extracts target projects/repos, defines acceptance criteria, detects ambiguity, and rejects unsafe or unclear tickets.

### Hermes-Manager

Enforces security, compliance, global policy, workflow gates, token/run anomaly checks, and final governance review.

### Hermes-ProjectManager

Owns workflow execution, task breakdown, worker sequencing, confidence debate participation, and delivery coordination.

### Hermes-{projectName}

Permanent project expert created only after project validation. It has two modes:

```text
Solo Maintainer Mode
  Used for high-confidence routine fixes.

Oracle Mode
  Used for complex work. Provides blast radius analysis, constraints,
  historical pitfalls, review, and veto authority.
```

### Hermes-Frontend

Handles UI, frontend routes, client state, frontend tests/builds, and frontend API integration.

### Hermes-Backend

Handles API endpoints, service logic, validation, backend tests, and backend framework conventions.

### Hermes-Database

Handles migrations, schema changes, seeders, data integrity, and query concerns.

### Hermes-QA

Runs tests, lint, builds, sandbox validation, reproduction checks, and acceptance criteria verification.

## Non-Responsibilities

Each profile must define what the bot may not do.

Examples:

```text
Hermes-QA
  May run tests and inspect results.
  May not silently patch source code unless explicitly assigned.

Hermes-Frontend
  May edit frontend paths.
  May not alter database migrations.

Hermes-Database
  May edit migrations, seeders, schema code.
  May not change UI behavior.

Hermes-{projectName}
  May veto project-inconsistent changes.
  May not expand its own permissions.
```

