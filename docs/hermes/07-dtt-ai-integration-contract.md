# DTT-AI Integration Contract

DTT-AI integration can come after the bots are defined, but `hermes-core` should be designed for it from the beginning.

## Boundary

```text
DTT-AI
  Human-facing control plane and terminal UI.

hermes-core
  AI orchestration, workflow, profiles, memory, policy, reporting.

hermes-runner
  Controlled execution, file/repo operations, commands, tests, interactive
  sessions.
```

DTT-AI should receive structured events and send human input or approval events back to Hermes.

## Contracts

```text
Event Stream
  Hermes publishes workflow, agent, policy, terminal, test, report, and memory
  events.

Command/Input API
  DTT-AI sends human answers, approvals, cancellations, and prompt responses.

Terminal Session Bridge
  hermes-runner exposes live stdout/stderr and accepts stdin when needed.
```

## Event Types

```text
workflow.created
workflow.state_changed
workflow.completed
workflow.failed

agent.started
agent.message
agent.completed
agent.failed

mad.score_submitted
mad.final_score_calculated
mad.topology_selected

policy.allowed
policy.denied
policy.escalation_required

terminal.session_started
terminal.stdout
terminal.stderr
terminal.prompt_detected
terminal.stdin_written
terminal.session_completed

human.input_required
human.input_received
human.approval_required
human.approval_received

repo.file_changed
repo.diff_ready
test.started
test.completed
sandbox.started
sandbox.url_ready

report.ready
learning.candidate_created
memory.promoted
```

## New Project Interaction

```text
DTT-AI/agent runtime invokes the larv:full skill.
DTT-AI displays skill/session output.
DTT-AI reports structured prompts when larv asks for input.
DTT-AI captures human answers to larv prompts.
DTT-AI reports output, prompts, and answers to Hermes Core.
Hermes Core records run state, transcript, prompt/answer history, and events.
DTT-AI reports completion and artifact location.
Hermes Core ingests artifacts and creates ProjectContextCandidate.
```

Hermes Core does not assume `larv:full` is a shell executable.

The reporting endpoints are:

```text
POST /workflows/new-project/larv-skill/session-started
POST /workflows/new-project/larv-skill/{session_id}/output
POST /workflows/new-project/larv-skill/{session_id}/prompt-shown
POST /workflows/new-project/larv-skill/{session_id}/human-answer
POST /workflows/new-project/larv-skill/{session_id}/completed
POST /workflows/new-project/larv-skill/{session_id}/failed
```

## Issue Fix Interaction

```text
Hermes runs workflow.
DTT-AI shows bot status and logs.
Sandbox URL becomes available.
report.ready is emitted.
Human reviews sandbox/report.
DTT-AI sends approval or rejection.
Hermes proceeds or revises.
```

## Availability Rule

Hermes should not depend on the DTT-AI browser being open.

Runs continue server-side. DTT-AI observes and intervenes when needed.

## Memory Ownership

DTT-AI is not the source of Hermes memory.

```text
DTT-AI displays memory, reports, and events.
hermes-core stores and governs them.
```
