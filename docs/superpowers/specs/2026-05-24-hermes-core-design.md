# Hermes Core Design

This spec indexes the approved Hermes architecture documentation.

The design is split into focused files under `docs/hermes/`:

```text
00-overview.md
01-core-components.md
02-new-project-workflow.md
03-issue-fix-workflow.md
04-agent-profiles.md
05-self-learning-memory.md
06-security-permissions.md
07-dtt-ai-integration-contract.md
08-first-proof-of-concept.md
09-interactive-session-resume.md
```

Key decisions:

```text
hermes-core is workflow-first, profile-backed, and sequential initially.
DTT-AI is the human-facing terminal/control plane.
hermes-runner performs controlled execution.
Agent profiles are structured manifests plus database-backed runtime state.
Specialized tactical workers are Hermes-Frontend, Hermes-Backend,
Hermes-Database, and Hermes-QA.
larv:full is an interactive discovery/scaffolding pipeline, not the entire
builder.
Permanent Hermes-{projectName} is created only after project completion and
validation.
Self-learning uses run notes, candidate learnings, and promoted memory.
Issue fixes require MAD confidence scoring and human checkpoint before PR/push.
Interactive larv:full sessions must be resumable by session ID.
```

