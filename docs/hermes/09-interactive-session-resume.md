# Resumable Interactive Sessions

Interactive commands and agent/skill sessions may ask questions mid-run. Hermes must treat this as normal workflow state, not as a broken connection.

For `larv:full` specifically:

```text
larv:full is a skill/agent-runtime workflow, not a shell executable.
DTT-AI or the agent runtime owns invocation.
Hermes Core records session metadata, output, answers, completion, and artifacts.
```

The design goal:

```text
DTT-AI can disconnect.
The human browser can disconnect.
The visual terminal can reconnect.
The Hermes interactive session remains durable server-side.
```

## Interactive Session Record

When Hermes starts an interactive command, the execution adapter creates an interactive session record.

```text
InteractiveSession
  id
  run_id
  workflow_type
  command
  working_directory
  process_id_or_pty_id
  status
  transcript_ref
  prompt_history
  last_prompt
  stdin_history
  created_at
  last_seen_at
```

Supported statuses:

```text
running
waiting_for_input
resumed
completed
failed
interrupted
recovery_required
expired
```

## External larv:full Skill Flow

```text
1. DTT-AI/agent runtime invokes larv:full.
2. DTT-AI reports session start to Hermes Core.
3. Hermes stores an InteractiveSessionRecord with command ["skill:larv:full"].
4. DTT-AI streams output chunks to Hermes Core.
5. Human answers prompts in DTT-AI.
6. DTT-AI reports prompt answers to Hermes Core.
7. DTT-AI reports completion and artifact location.
8. Hermes ingests artifacts and creates ProjectContextCandidate.
```

## Shell Command Flow

```text
1. Hermes-ProjectManager starts an interactive shell command.
2. hermes-runner opens a persistent PTY/SSH-backed process.
3. Session ID is stored immediately.
4. stdout/stderr are streamed and appended to transcript storage.
5. When the command asks a question, prompt detection marks the session as
   waiting_for_input.
6. DTT-AI displays the question to the human.
7. Human submits an answer.
8. DTT-AI sends session_id + answer to hermes-core/hermes-runner.
9. hermes-runner writes the answer to the same PTY stdin.
10. Workflow continues.
```

## Resume vs Restart

```text
Resume connection != restart larv:full
```

The preferred behavior is to keep the same process alive while waiting for input.

DTT-AI may reconnect visually, but the backend session should remain alive.

If the underlying SSH connection or process dies, Hermes must not blindly restart. It should mark the session as interrupted and let Hermes-ProjectManager decide whether recovery is possible from artifacts and transcript.

## Workflow States

New project creation should include:

```text
larv_full_session_started
larv_full_waiting_for_input
larv_full_input_received
larv_full_resumed
larv_full_completed
larv_full_interrupted
larv_full_recovery_required
```

## Prompt Detection

Initial prompt detection can use:

```text
known prompt markers
question-like output
process idle state
input expected heuristics
```

Longer-term, `larv:full` should emit structured prompt events.

Example future event:

```json
{
  "type": "prompt.required",
  "session_id": "sess_123",
  "prompt_id": "project_stack_choice",
  "question": "Which stack do you want?",
  "options": ["Laravel", "Fastify", "Next.js"],
  "input_type": "single_choice"
}
```

## Stdin Replay Protection

Hermes must record submitted answers so the same human input is not accidentally replayed after a reconnect.

Each submitted answer should include:

```text
session_id
prompt_id when available
answer
submitted_by
submitted_at
stdin_write_id
```

If `prompt_id` is unavailable, Hermes should use the active session state and last prompt hash to reduce duplicate writes.

## Transcript Storage

Hermes stores:

```text
stdout
stderr
prompt history
human answers
state transitions
warnings
errors
completion status
```

The transcript supports audit, artifact ingestion, recovery decisions, and future project memory distillation.
