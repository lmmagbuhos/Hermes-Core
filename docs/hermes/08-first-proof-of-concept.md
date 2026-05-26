# First Proof of Concept

The first proof must execute real workflows. It must not be a fake MVP, simulated bot demo, or UI-only prototype.

## POC A: New Project Creation

Status: **Core runtime loop proven on 2026-05-26.**

Goal:

```text
Use DTT-AI/agent runtime to invoke the real larv:full skill while Hermes records
the session, ingests the result, validates it, and creates a permanent project
agent.
```

Required behavior:

```text
1. Human submits a new project request.
2. Hermes-Triage normalizes it.
3. Hermes-Manager checks stack/policy requirements.
4. DTT-AI/agent runtime invokes the larv:full skill.
5. Human answers larv:full prompts through DTT-AI.
6. DTT-AI reports transcript/output/answers/completion to Hermes.
7. Hermes ingests larv artifacts and transcript.
8. Hermes creates ProjectContextCandidate.
9. Hermes-ProjectManager creates sequential worker tasks.
10. Hermes-Frontend, Hermes-Backend, and Hermes-Database run only if needed.
11. Hermes-QA validates tests/build/sandbox.
12. Hermes-Manager produces final review.
13. Permanent Hermes-{projectName} is created after validation.
14. Learning candidates are created.
15. Completion report is produced.
```

Proven so far:

```text
DTT-AI New Project page starts a real SSH/tmux Codex session.
Codex runs in YOLO mode inside the remote project directory.
DTT-AI invokes larv:full as the accepted plain-text Codex skill trigger.
DTT-AI displays real larv output in the browser.
larv asks a real workflow question.
The human answers through the DTT-AI browser UI.
DTT-AI sends the answer through the backend answer endpoint.
The same tmux/Codex session continues after the answer.
larv creates docs/larv/STATE.yaml and produces website/sandbox output.
Hermes lifecycle reporting is wrapped around the proven runtime path behind HERMES_ENABLED=true.
```

Remaining POC A productization:

```text
durable New Project session persistence
project cards and reconnect/resume behavior
operator UX polish for question display, output filtering, loading states, and runtime details
final operator documentation
full completion-to-ProjectContextCandidate smoke with Hermes enabled when quota allows
```

This proves:

```text
interactive project discovery
real larv skill invocation through DTT-AI/agent runtime
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
