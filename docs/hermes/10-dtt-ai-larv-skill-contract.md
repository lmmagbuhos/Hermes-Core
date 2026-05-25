# DTT-AI Larv Skill Contract

This document defines how DTT-AI connects to Hermes Core when DTT-AI invokes the `larv:full` skill.

## Ownership Boundary

```text
DTT-AI / agent runtime
  Invokes larv:full.
  Displays skill output to the human.
  Collects human answers to larv prompts.
  Reports lifecycle events to Hermes Core.

Hermes Core
  Does not invoke larv:full directly.
  Records workflow state, session metadata, output, answers, and completion.
  Ingests generated artifacts from the reported project directory.
  Creates ProjectContextCandidate.
```

## Base URL

Use the Hermes Core service URL configured for the environment.

Example local development URL:

```text
http://127.0.0.1:8000
```

## Authentication

When `HERMES_DTT_AI_SHARED_TOKEN` is configured in Hermes Core, every DTT-AI contract request must include:

```http
X-Hermes-Token: <shared-token>
```

Hermes returns `401` when the token is missing or incorrect. Local development can leave `HERMES_DTT_AI_SHARED_TOKEN` empty to disable this check.

## Idempotency

Every lifecycle request should include a stable `event_id`.

```json
{
  "event_id": "dtt-session-123-output-000001"
}
```

Rules:

```text
event_id must be globally unique per DTT-AI event.
DTT-AI should reuse the same event_id when retrying the same request.
Hermes returns the previously recorded response with idempotent_replay = true for duplicate event_id values.
Hermes does not re-append duplicate output chunks when event_id is replayed.
```

## Sequence

DTT-AI should call the endpoints in this order:

```text
1. POST /workflows/new-project/larv-skill/session-started
2. POST /workflows/new-project/larv-skill/{session_id}/output
3. POST /workflows/new-project/larv-skill/{session_id}/prompt-shown
4. POST /workflows/new-project/larv-skill/{session_id}/human-answer
5. Repeat output, prompt-shown, and human-answer as needed
6. POST /workflows/new-project/larv-skill/{session_id}/completed
```

If the `larv:full` skill crashes, is cancelled, or cannot continue, call:

```text
POST /workflows/new-project/larv-skill/{session_id}/failed
```

Hermes returns its own `interactive_session.id`. Use that value as `{session_id}` in later calls.

## 1. Session Started

Call this immediately after DTT-AI starts the `larv:full` skill.

```http
POST /workflows/new-project/larv-skill/session-started
Content-Type: application/json
X-Hermes-Token: <shared-token>
```

Request:

```json
{
  "event_id": "dtt-session-123-started",
  "project_name": "AeroTrack",
  "external_session_id": "dtt-session-123",
  "cwd": "/home/projects/AeroTrack"
}
```

Fields:

```text
event_id
  Stable DTT-AI event identifier for idempotent retries.

project_name
  Human-readable project name.

external_session_id
  DTT-AI or agent-runtime session ID. Hermes stores this for correlation.

cwd
  Project working directory or expected artifact root.
```

Response:

```json
{
  "run": {
    "id": 1,
    "workflow_type": "new_project_creation",
    "state": "larv_full_session_started",
    "payload": {
      "project_name": "AeroTrack",
      "cwd": "/home/projects/AeroTrack",
      "external_larv_session_id": "dtt-session-123",
      "invocation_owner": "dtt_ai_agent_runtime",
      "interactive_session_id": "sess_abc"
    }
  },
  "interactive_session": {
    "id": "sess_abc",
    "run_id": 1,
    "command": ["skill:larv:full"],
    "cwd": "/home/projects/AeroTrack",
    "status": "running",
    "last_prompt": null,
    "transcript_ref": "/home/projects/AeroTrack/.hermes/transcripts/run_1.log"
  },
  "idempotent_replay": false
}
```

## 2. Output Chunk

Call this whenever DTT-AI receives output from the skill/agent session.

```http
POST /workflows/new-project/larv-skill/{session_id}/output
Content-Type: application/json
X-Hermes-Token: <shared-token>
```

Request:

```json
{
  "event_id": "dtt-session-123-output-000001",
  "sequence": 1,
  "stream": "stdout",
  "output": "Which backend stack should be used?"
}
```

Fields:

```text
event_id
  Stable DTT-AI event identifier for idempotent retries.

sequence
  Monotonically increasing output chunk number within the external DTT-AI session.

stream
  Output source label. Use stdout, stderr, or agent.

output
  Raw text chunk to append to Hermes transcript.
```

Response:

```json
{
  "run": {
    "id": 1,
    "workflow_type": "new_project_creation",
    "state": "larv_full_session_started",
    "payload": {}
  },
  "interactive_session": {
    "id": "sess_abc",
    "run_id": 1,
    "command": ["skill:larv:full"],
    "cwd": "/home/projects/AeroTrack",
    "status": "running",
    "last_prompt": null,
    "transcript_ref": "/home/projects/AeroTrack/.hermes/transcripts/run_1.log"
  },
  "idempotent_replay": false
}
```

## 3. Prompt Shown

Call this when DTT-AI detects that `larv:full` is asking the human for input.

```http
POST /workflows/new-project/larv-skill/{session_id}/prompt-shown
Content-Type: application/json
X-Hermes-Token: <shared-token>
```

Request:

```json
{
  "event_id": "dtt-session-123-prompt-stack-choice-001",
  "prompt_id": "stack-choice-001",
  "prompt": "Which backend stack should be used?",
  "choices": ["Fastify", "Laravel"],
  "default": "Fastify",
  "is_required": true,
  "metadata": {
    "source": "larv:full",
    "phase": "stack-selection"
  }
}
```

Fields:

```text
event_id
  Stable DTT-AI event identifier for idempotent retries.

prompt_id
  DTT-AI prompt identifier. Must be stable per prompt.

prompt
  Exact prompt text shown to the human.

choices
  Optional list of selectable answers when DTT-AI can detect them.

default
  Optional default answer when DTT-AI can detect one.

is_required
  Whether DTT-AI should block the workflow until a human answer is submitted.

metadata
  Optional structured context such as source, phase, UI control type, or raw parser details.
```

Response state:

```text
run.state = larv_full_waiting_for_input
interactive_session.status = waiting_for_input
interactive_session.last_prompt = prompt
```

## 4. Human Answer

Call this after the human answers a `larv:full` prompt in DTT-AI.

```http
POST /workflows/new-project/larv-skill/{session_id}/human-answer
Content-Type: application/json
X-Hermes-Token: <shared-token>
```

Request:

```json
{
  "event_id": "dtt-session-123-answer-stack-choice-001",
  "prompt_id": "stack-choice-001",
  "answer": "Fastify and Next.js"
}
```

Fields:

```text
event_id
  Stable DTT-AI event identifier for idempotent retries.

prompt_id
  DTT-AI prompt identifier. Must be stable per prompt.

answer
  Human answer submitted to larv:full.
```

Response state:

```text
run.state = larv_full_input_received
```

Hermes records this answer for audit and replay protection. DTT-AI remains responsible for sending the answer to the actual `larv:full` skill runtime.

## 5. Completed

Call this when the `larv:full` skill finishes and generated artifacts are available.

```http
POST /workflows/new-project/larv-skill/{session_id}/completed
Content-Type: application/json
X-Hermes-Token: <shared-token>
```

Request:

```json
{
  "event_id": "dtt-session-123-completed",
  "project_dir": "/home/projects/AeroTrack"
}
```

Fields:

```text
event_id
  Stable DTT-AI event identifier for idempotent retries.

project_dir
  Directory where larv generated project docs/code/artifacts.
  Hermes Core must be able to read this path.
```

Response state:

```text
run.state = project_context_candidate_created
```

Hermes will:

```text
1. mark the recorded larv skill session completed
2. read the transcript file
3. ingest generated artifacts
4. create HermesProjectBlueprint
5. create ProjectContextCandidate
```

If Hermes Core cannot ingest `project_dir`, it returns `400` with structured validation detail and does not mark the session completed.

Example error:

```json
{
  "detail": {
    "code": "project_dir_missing",
    "message": "Project directory does not exist: /home/projects/AeroTrack",
    "path": "/home/projects/AeroTrack"
  }
}
```

Error codes:

```text
project_dir_missing
  The reported path does not exist from the Hermes Core process.

project_dir_not_directory
  The reported path exists but is a file or non-directory path.

project_dir_not_readable
  Hermes Core cannot list/read the reported directory.

transcript_not_readable
  Hermes Core recorded a transcript path but cannot read it during completion.

artifact_ingestion_failed
  Hermes Core reached the project directory but failed while parsing generated artifacts.
```

## 6. Failed

Call this when DTT-AI knows the `larv:full` skill cannot continue.

```http
POST /workflows/new-project/larv-skill/{session_id}/failed
Content-Type: application/json
X-Hermes-Token: <shared-token>
```

Request:

```json
{
  "event_id": "dtt-session-123-failed",
  "reason": "larv skill crashed before artifact generation"
}
```

Fields:

```text
event_id
  Stable DTT-AI event identifier for idempotent retries.

reason
  Human-readable failure reason captured by DTT-AI.
```

Response state:

```text
run.state = failed
interactive_session.status = recovery_required
```

## Artifact Access Requirement

Hermes Core must be able to read `project_dir`.

If DTT-AI and Hermes Core run on the same server, pass the local filesystem path.

If DTT-AI and Hermes Core run on different servers, DTT-AI must provide one of:

```text
shared mounted storage path
downloadable artifact bundle
artifact upload endpoint
repository URL/branch after generation
```

The current Hermes implementation expects a readable local `project_dir`.

## Remaining Limitations

The current API now supports shared-token auth, idempotency, output sequencing metadata, stream labels, structured prompt metadata, failure reporting, and artifact path validation. Remaining contract gaps:

```text
artifact upload endpoint for non-shared filesystems
repository URL ingestion for generated projects
```

## Minimal DTT-AI Pseudocode

```python
import requests

HERMES = "http://127.0.0.1:8000"
HEADERS = {"X-Hermes-Token": HERMES_TOKEN}

started = requests.post(
    f"{HERMES}/workflows/new-project/larv-skill/session-started",
    headers=HEADERS,
    json={
        "event_id": f"{dtt_session_id}-started",
        "project_name": "AeroTrack",
        "external_session_id": dtt_session_id,
        "cwd": project_dir,
    },
).json()

session_id = started["interactive_session"]["id"]
sequence = 0

def on_larv_output(text: str):
    global sequence
    sequence += 1
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/output",
        headers=HEADERS,
        json={
            "event_id": f"{dtt_session_id}-output-{sequence:06d}",
            "sequence": sequence,
            "stream": "stdout",
            "output": text,
        },
    )

def on_prompt_shown(prompt_id: str, prompt: str, choices: list[str] | None = None):
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/prompt-shown",
        headers=HEADERS,
        json={
            "event_id": f"{dtt_session_id}-prompt-{prompt_id}",
            "prompt_id": prompt_id,
            "prompt": prompt,
            "choices": choices or [],
            "is_required": True,
            "metadata": {"source": "larv:full"},
        },
    )

def on_human_answer(prompt_id: str, answer: str):
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/human-answer",
        headers=HEADERS,
        json={
            "event_id": f"{dtt_session_id}-answer-{prompt_id}",
            "prompt_id": prompt_id,
            "answer": answer,
        },
    )

def on_larv_completed(project_dir: str):
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/completed",
        headers=HEADERS,
        json={
            "event_id": f"{dtt_session_id}-completed",
            "project_dir": project_dir,
        },
    )

def on_larv_failed(reason: str):
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/failed",
        headers=HEADERS,
        json={
            "event_id": f"{dtt_session_id}-failed",
            "reason": reason,
        },
    )
```
