# Project Hermes Overview

Project Hermes is a no-touch software maintenance and project initialization system. Its goal is to automate routine code maintenance, bug fixing, refactoring, validation, and new project setup while keeping humans in high-level approval and interactive-input roles.

Hermes is not the DTT-AI website and not merely an SSH terminal wrapper. Hermes is the AI operating layer behind the work.

## Core Boundary

```text
DTT-AI
  Human-facing control plane.
  Displays live terminal sessions, workflow state, bot activity, reports, approvals,
  sandbox URLs, and interactive prompts.

hermes-core
  AI orchestration and memory layer.
  Owns agent profiles, workflow state, confidence scoring, policy checks,
  self-learning records, reports, and execution decisions.

hermes-runner
  Execution layer.
  Performs controlled file/repo operations, command execution, tests, sandbox
  startup, and interactive terminal sessions.
```

## First Version Principle

The first version must not be a fake MVP. It must prove real vertical workflows:

```text
1. Create one real project through larv:full.
2. Fix one real issue in an existing project.
```

Parallel tactical workers are deferred, but worker identities are not. Hermes should use specialized tactical profiles from day one, executed sequentially at first:

```text
Hermes-Frontend
Hermes-Backend
Hermes-Database
Hermes-QA
```

## Core Agent Roles

```text
Hermes-Triage
  Normalizes requests, extracts repositories/projects, defines acceptance
  criteria, and rejects ambiguity.

Hermes-Manager
  Enforces security, compliance, institutional standards, workflow policy,
  token/run anomaly checks, and final governance gates.

Hermes-ProjectManager
  Orchestrates per-ticket or per-project workflows, creates worker plans,
  coordinates tactical agents, and participates in confidence debate.

Hermes-{projectName}
  Permanent project expert created only after a project is completed and
  validated. Acts as Solo Maintainer for high-confidence fixes or Context
  Oracle for complex fixes.

Hermes-Frontend
  Handles frontend implementation within scoped permissions.

Hermes-Backend
  Handles backend implementation within scoped permissions.

Hermes-Database
  Handles migrations, schema, seeders, data integrity, and database concerns.

Hermes-QA
  Runs validation, checks acceptance criteria, verifies sandbox behavior, and
  reports failures.
```

## Confidence Gate

For maintenance work, Hermes uses Multi-Agent Debate between Hermes-ProjectManager and Hermes-{projectName}.

```text
C_Final = min(C_PM, C_Project)
```

If `C_Final >= 90`, Hermes-{projectName} may use Solo Maintainer Mode.

If `C_Final < 90`, Hermes-ProjectManager controls the Assembly Line and Hermes-{projectName} acts as Context Oracle, Technical Advisor, Legacy Guardrail, and final diff reviewer.

## Self-Learning Principle

Hermes should learn continuously but promote durable memory carefully.

```text
Hermes may observe continuously.
Hermes may propose learnings automatically.
Hermes promotes durable memory only through scoped evidence rules.
```

Hermes can learn facts automatically when evidence is strong. It can propose broader project patterns. It cannot autonomously expand its own authority, weaken policy, skip approval gates, or rewrite governance rules.

