# Core Components

`hermes-core` should be built as a workflow-first, profile-backed, sequential multi-agent runtime.

## Agent Profile Registry

Stores structured Hermes bot identities:

```text
Hermes-Triage
Hermes-Manager
Hermes-ProjectManager
Hermes-{projectName}
Hermes-Frontend
Hermes-Backend
Hermes-Database
Hermes-QA
```

Profiles define:

```text
identity
role contract
responsibilities
non-responsibilities
permissions
allowed tools
denied tools
memory access
confidence rubric
escalation rules
review authority
learning authority
runtime model config
profile version
```

## Runtime Prompt Compiler

Builds agent invocation context from:

```text
agent profile
workflow state
ticket/request data
project memory
relevant files/artifacts
allowed tools
current constraints
```

The profile is the source of truth. Runtime prompts are generated from profiles and current context.

## Run-State Engine

Owns workflow progression for:

```text
new_project_creation
issue_fix
```

It records:

```text
state transitions
agent decisions
confidence scores
tool calls
terminal sessions
test results
reports
learning candidates
human approval checkpoints
```

The first implementation should use a simple explicit run-state model, not a general-purpose workflow engine.

## Execution Adapter

The controlled interface between Hermes reasoning and real work.

Capabilities include:

```text
repo.read_file
repo.search
repo.apply_patch
repo.diff
repo.status
repo.commit
terminal.run_command
terminal.start_interactive
terminal.write_stdin
sandbox.start
test.run
```

Structured tools should be used for file intelligence and precise edits. Terminal sessions should be used for runtime execution, test commands, scaffolding, and interactive CLIs such as `larv:full`.

## Memory System

Stores:

```text
run notes
candidate learnings
promoted project memory
global policy memory
agent-specific calibration records
```

Memory should use structured records first, with vector/search retrieval added later.

## Policy and Permission Layer

Checks whether an agent can perform an action based on:

```text
agent role
workflow
file scope
command risk
project risk
approval state
environment
```

Policy returns:

```text
allowed
denied
needs_escalation
needs_human_approval
needs_manager_approval
```

## Reporting and Review Layer

Produces human-readable reports, especially before PR/push.

Issue-fix reports must include:

```text
summary
files changed
tests run
sandbox URL
risks
unresolved items
recommended PR action
```

## Event Log

Every important action emits an event. DTT-AI will later consume these events.

Examples:

```text
workflow.state_changed
agent.started
agent.completed
mad.final_score_calculated
terminal.stdout
terminal.prompt_detected
human.input_required
test.completed
report.ready
learning.candidate_created
```

