# New Project Creation Workflow

For new projects, `larv:full` is the interactive discovery and scaffolding pipeline, not the whole builder.

## Workflow

```text
1. Request received
2. Hermes-Triage normalization
3. Hermes-Manager policy check
4. Hermes-ProjectManager starts larv:full
5. Human interacts with larv:full
6. Larv artifact ingestion
7. ProjectContextCandidate created
8. ProjectManager creates worker plan
9. Tactical workers execute sequentially as needed
10. Hermes-QA validates
11. Hermes-Manager final review
12. Permanent Hermes-{projectName} created
13. Learning candidates created
14. Completion report produced
```

## Request Received

A human submits a request such as:

```text
Create AeroTrack with Fastify and Next.js.
```

## Hermes-Triage Normalization

Triage extracts:

```text
project name
intended stack
unclear requirements
initial acceptance criteria
repo topology preference
```

If the request is too vague, Triage rejects it or asks for clarification.

## Hermes-Manager Policy Check

Manager validates:

```text
allowed stack
required institutional defaults
security requirements
standard auth/config expectations
forbidden technologies or risky choices
```

## larv:full Execution

Hermes-ProjectManager starts `larv:full` through the execution adapter.

`larv:full` asks project-shaping questions. DTT-AI later displays the terminal session and lets the human answer prompts.

Hermes stores:

```text
terminal transcript
prompt/answer history
generated files
generated docs
warnings and errors
```

## Artifact Ingestion

After `larv:full` completes, Hermes reads:

```text
generated docs
handoff files
architecture notes
implementation slices
generated code
terminal transcript
```

Hermes produces:

```text
HermesProjectBlueprint
```

The blueprint contains:

```text
project_name
repo_topology
frontend_stack
backend_stack
required_packages
domain_summary
architecture_decisions
implementation_slices
test_commands
sandbox_commands
unresolved_questions
risk_flags
worker_task_queue
```

## ProjectContextCandidate

Hermes creates a temporary project context during creation.

This candidate may contain uncertainty and messy creation history. It is not the permanent self-learning project agent.

## Sequential Tactical Worker Execution

Hermes-ProjectManager converts the blueprint into sequential worker tasks.

Workers run only when relevant:

```text
Hermes-Backend
  Backend code, APIs, services, auth usage, backend tests.

Hermes-Frontend
  UI routes, components, client state, frontend API integration.

Hermes-Database
  Migrations, seeders, schema, data integrity.

Hermes-QA
  Tests, lint, builds, sandbox checks, acceptance criteria.
```

The first version defers parallelism but keeps specialization.

## Permanent Project Agent Creation

Permanent `Hermes-{projectName}` is created only after the project is completed and validated.

It receives distilled memory:

```text
validated architecture
repo layout
stack
commands
known constraints
accepted project decisions
initial patch/build history
```

Raw creation transcripts remain archived but are not loaded by default.

