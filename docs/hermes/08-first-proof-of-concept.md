# First Proof of Concept

The first proof must execute real workflows. It must not be a fake MVP, simulated bot demo, or UI-only prototype.

## POC A: New Project Creation

Goal:

```text
Use Hermes to create one real project through larv:full, ingest the result,
validate it, and create a permanent project agent.
```

Required behavior:

```text
1. Human submits a new project request.
2. Hermes-Triage normalizes it.
3. Hermes-Manager checks stack/policy requirements.
4. Hermes-ProjectManager runs larv:full.
5. Human answers larv:full prompts through an interactive terminal session.
6. Hermes ingests larv artifacts and transcript.
7. Hermes creates ProjectContextCandidate.
8. Hermes-ProjectManager creates sequential worker tasks.
9. Hermes-Frontend, Hermes-Backend, and Hermes-Database run only if needed.
10. Hermes-QA validates tests/build/sandbox.
11. Hermes-Manager produces final review.
12. Permanent Hermes-{projectName} is created after validation.
13. Learning candidates are created.
14. Completion report is produced.
```

This proves:

```text
interactive project discovery
real command execution
artifact ingestion
workflow state
profile-backed agents
validation
project-agent creation
memory candidate generation
```

## POC B: Issue Fix

Goal:

```text
Use Hermes to fix one real issue in a real existing project.
```

Required behavior:

```text
1. Human submits issue ticket.
2. Hermes-Triage normalizes issue and acceptance criteria.
3. Hermes loads Hermes-{projectName}.
4. Hermes-ProjectManager and Hermes-{projectName} perform MAD confidence scoring.
5. C_Final = min(C_PM, C_Project).
6. Hermes chooses Solo Maintainer or Assembly Line mode.
7. Correct agent applies real code changes.
8. Hermes-QA runs relevant tests/build/sandbox checks.
9. Hermes-{projectName} reviews diff.
10. Hermes-Manager audits.
11. Hermes produces report + sandbox URL.
12. Human confirms before PR/push.
13. Learning candidates are created after validation.
```

This proves:

```text
ticket normalization
project memory use
confidence debate
solo vs assembly topology
real patch execution
verification
human approval checkpoint
learning candidate creation
```

## Deferred

```text
parallel tactical workers
full DTT-AI integration
GitHub PR automation
Linear webhook support
advanced vector retrieval
fully automated memory governance
multi-project fleet scaling
production deployment
```

## Must Not Be Faked

```text
agent profiles
workflow states
real command execution
real file changes
real validation
real reports
learning records
```

