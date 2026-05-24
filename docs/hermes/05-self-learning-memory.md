# Self-Learning Memory

Hermes self-learning should be real, staged, evidence-backed, and permission-bound.

## Core Rule

```text
Hermes may observe continuously.
Hermes may propose learnings automatically.
Hermes promotes durable memory only through scoped evidence rules.
```

## Memory Stages

```text
Run Notes
  Temporary memory created during an active workflow.

Candidate Learnings
  Structured lessons proposed after validation, failure, merge, or approval.

Promoted Memory
  Durable memory available to future Hermes runs.

Deprecated/Rejected Memory
  Memory that should no longer influence agents.
```

## Memory Scopes

```text
global
agent
project
repo_path
workflow
ticket/run
```

## Promotion Lanes

### Lane 1: Auto-Promoted Facts

Narrow, evidence-backed, low-risk facts.

Examples:

```text
package manager
test command
framework version
repo structure
sandbox startup command
```

### Lane 2: Manager-Reviewed Project Patterns

Broader lessons that influence future fixes.

Examples:

```text
preferred implementation patterns
repeated failure modes
project-specific testing expectations
fragile modules
```

### Lane 3: Governance-Gated Behavior Changes

Anything that changes authority, policy, security, or agent behavior.

Examples:

```text
permission expansion
skipping approval checkpoints
modifying security rules
changing confidence thresholds
```

## Memory Record Shape

```text
MemoryRecord
  id
  type
  scope
  summary
  details
  status
  confidence
  evidence_refs
  source_run_id
  source_ticket_id
  source_commit_or_pr
  created_by_agent
  reviewed_by
  created_at
  review_after
```

## Project Agent Memory

Permanent `Hermes-{projectName}` loads:

```text
promoted project memory
relevant repo_path memory
current ticket context
recent successful fix summaries
known constraints
```

It does not load raw transcripts by default.

## New Project Creation

During project creation, Hermes uses `ProjectContextCandidate`.

After validation, Hermes distills clean project memory and creates permanent `Hermes-{projectName}`.

## Safety Rule

```text
Hermes can learn what is true.
Hermes can propose what should be preferred.
Hermes cannot autonomously grant itself more power.
```

