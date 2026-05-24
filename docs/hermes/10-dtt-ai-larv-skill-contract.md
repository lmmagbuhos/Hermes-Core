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

## Sequence

DTT-AI should call the endpoints in this order:

```text
1. POST /workflows/new-project/larv-skill/session-started
2. POST /workflows/new-project/larv-skill/{session_id}/output
3. POST /workflows/new-project/larv-skill/{session_id}/human-answer
4. Repeat output and human-answer as needed
5. POST /workflows/new-project/larv-skill/{session_id}/completed
```

Hermes returns its own `interactive_session.id`. Use that value as `{session_id}` in later calls.

## 1. Session Started

Call this immediately after DTT-AI starts the `larv:full` skill.

```http
POST /workflows/new-project/larv-skill/session-started
Content-Type: application/json
```

Request:

```json
{
  "project_name": "AeroTrack",
  "external_session_id": "dtt-session-123",
  "cwd": "/home/projects/AeroTrack"
}
```

Fields:

```text
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
  }
}
```

## 2. Output Chunk

Call this whenever DTT-AI receives output from the skill/agent session.

```http
POST /workflows/new-project/larv-skill/{session_id}/output
Content-Type: application/json
```

Request:

```json
{
  "output": "Which backend stack should be used?"
}
```

Current fields:

```text
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
  }
}
```

## 3. Human Answer

Call this after the human answers a `larv:full` prompt in DTT-AI.

```http
POST /workflows/new-project/larv-skill/{session_id}/human-answer
Content-Type: application/json
```

Request:

```json
{
  "prompt_id": "stack-choice-001",
  "answer": "Fastify and Next.js"
}
```

Fields:

```text
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

## 4. Completed

Call this when the `larv:full` skill finishes and generated artifacts are available.

```http
POST /workflows/new-project/larv-skill/{session_id}/completed
Content-Type: application/json
```

Request:

```json
{
  "project_dir": "/home/projects/AeroTrack"
}
```

Fields:

```text
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

## Current Limitations

The current API records core lifecycle events. The next hardening pass should add:

```text
auth/shared token
idempotency keys
output sequence numbers
stdout/stderr/agent stream labels
failed/interrupted endpoint
artifact path validation details
structured prompt metadata
```

## Minimal DTT-AI Pseudocode

```python
import requests

HERMES = "http://127.0.0.1:8000"

started = requests.post(
    f"{HERMES}/workflows/new-project/larv-skill/session-started",
    json={
        "project_name": "AeroTrack",
        "external_session_id": dtt_session_id,
        "cwd": project_dir,
    },
).json()

session_id = started["interactive_session"]["id"]

def on_larv_output(text: str):
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/output",
        json={"output": text},
    )

def on_human_answer(prompt_id: str, answer: str):
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/human-answer",
        json={"prompt_id": prompt_id, "answer": answer},
    )

def on_larv_completed(project_dir: str):
    requests.post(
        f"{HERMES}/workflows/new-project/larv-skill/{session_id}/completed",
        json={"project_dir": project_dir},
    )
```

