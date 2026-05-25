# DTT-AI Handoff

This is the practical integration handoff for wiring DTT-AI to Hermes Core for the external `larv:full` skill flow.

## Scope

DTT-AI owns the actual `larv:full` skill invocation and the human-facing terminal UI.

Hermes Core owns durable workflow state, transcript storage, prompt and answer audit history, artifact ingestion, and ProjectContextCandidate creation.

Hermes Core does not call `larv:full` directly.

## Environment

Hermes Core:

```text
HERMES_DATABASE_URL=sqlite:///./hermes.db
HERMES_DTT_AI_SHARED_TOKEN=<shared-token>
```

DTT-AI:

```text
HERMES_URL=https://<hermes-core-host>
HERMES_DTT_AI_SHARED_TOKEN=<same-shared-token>
```

When `HERMES_DTT_AI_SHARED_TOKEN` is set in Hermes Core, DTT-AI must send:

```http
X-Hermes-Token: <shared-token>
```

## Required Event Order

```text
1. DTT-AI starts the real larv:full skill in its agent/runtime environment.
2. DTT-AI reports session-started to Hermes Core.
3. DTT-AI streams output chunks to Hermes Core.
4. When larv asks for input, DTT-AI reports prompt-shown to Hermes Core.
5. The human answers in DTT-AI.
6. DTT-AI sends the answer to the running larv skill/runtime.
7. DTT-AI reports human-answer to Hermes Core.
8. DTT-AI repeats output, prompt-shown, and human-answer as needed.
9. DTT-AI reports completed with a readable artifact path, or failed with a reason.
```

Hermes returns `interactive_session.id` from `session-started`. DTT-AI must use that ID for every later request.

## Endpoints

```text
POST /workflows/new-project/larv-skill/session-started
POST /workflows/new-project/larv-skill/{session_id}/output
POST /workflows/new-project/larv-skill/{session_id}/prompt-shown
POST /workflows/new-project/larv-skill/{session_id}/human-answer
POST /workflows/new-project/larv-skill/{session_id}/completed
POST /workflows/new-project/larv-skill/{session_id}/failed
GET  /workflows/new-project/larv-skill/{session_id}/status
```

The full request and response contract is in `10-dtt-ai-larv-skill-contract.md`.

## Python Adapter

Hermes Core includes a small Python adapter that DTT-AI can copy, vendor, or import when both projects share the same Python environment:

```text
src/hermes_core/integrations/dtt_ai/client.py
```

The adapter exposes:

```python
from hermes_core.integrations.dtt_ai import DttAiEventIdFactory, DttAiHermesClient

event_ids = DttAiEventIdFactory("dtt-session-123")

with DttAiHermesClient(
    base_url="http://127.0.0.1:8000",
    token="<shared-token>",
    event_ids=event_ids,
) as hermes:
    session = hermes.start_larv_skill_session(
        project_name="AeroTrack",
        external_session_id="dtt-session-123",
        cwd="/home/dtt-ai/workspaces/AeroTrack",
    )
    hermes.record_output(
        session_id=session.id,
        sequence=1,
        stream="stdout",
        output="Which backend stack should be used?",
    )
    hermes.record_prompt_shown(
        session_id=session.id,
        prompt_id="stack-choice-001",
        prompt="Which backend stack should be used?",
        choices=["Fastify", "Laravel"],
        default="Fastify",
        metadata={"source": "larv:full"},
    )
    hermes.record_human_answer(
        session_id=session.id,
        prompt_id="stack-choice-001",
        answer="Fastify",
    )
    hermes.complete_session(
        session_id=session.id,
        project_dir="/home/dtt-ai/workspaces/AeroTrack",
    )
    status = hermes.get_session_status(session_id=session.id)
```

The client raises `httpx.HTTPStatusError` for Hermes error responses. DTT-AI should catch that exception, log the response body, and show the failure in the operator UI.

## Idempotency Rules

Every DTT-AI event should include `event_id`.

Use stable event IDs:

```text
<dtt-session-id>-started
<dtt-session-id>-output-000001
<dtt-session-id>-prompt-<prompt-id>
<dtt-session-id>-answer-<prompt-id>
<dtt-session-id>-completed
<dtt-session-id>-failed
```

Retry the same request with the same `event_id`. Hermes will return the previous response with `idempotent_replay = true`.

DTT-AI must not create a new `event_id` when retrying the same event.

## Prompt Handling

For every input prompt, DTT-AI should report `prompt-shown` before reporting `human-answer`.

Required fields:

```text
prompt_id
prompt
```

Recommended fields:

```text
choices
default
is_required
metadata.source = larv:full
metadata.phase = <detected larv phase when known>
```

DTT-AI remains responsible for sending the answer to the actual running `larv:full` runtime. Hermes records the answer for audit, recovery, and future learning.

## Status and Reloads

DTT-AI should call `get_session_status` when rendering run status cards or recovering after a browser reload.

The status response includes:

```text
run.state
interactive_session.status
interactive_session.last_prompt
interactive_session.prompt_history
interactive_session.stdin_history
interactive_session.transcript_ref
recent events
project_context_candidate when created
```

Use this endpoint for display and diagnostics. Do not use it as a replacement for sending lifecycle events; DTT-AI must still report output, prompts, answers, completion, and failure as they happen.

## Artifact Requirement

For `completed`, Hermes Core must be able to read `project_dir`.

This works when DTT-AI and Hermes Core share the same filesystem or mounted storage.

If completion fails, Hermes returns a structured `400` error. DTT-AI should show the `detail.message` to the operator and log `detail.code` plus `detail.path`.

Expected artifact error codes:

```text
project_dir_missing
project_dir_not_directory
project_dir_not_readable
transcript_not_readable
artifact_ingestion_failed
```

If they do not share a filesystem, do not call `completed` with a private DTT-AI-local path. The next contract extension should be one of:

```text
artifact upload endpoint
shared artifact bundle path
repository URL/branch ingestion
```

## Environment Validation

Before wiring a real `larv:full` run, validate the same-server connection from the Hermes Core checkout:

```bash
PYTHONPATH=src uvicorn hermes_core.app:app --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
HERMES_URL=http://127.0.0.1:8000 \
HERMES_DTT_AI_SHARED_TOKEN=<shared-token> \
python3 tools/validate_dtt_ai_environment.py \
  --workspace-path /home/dtt-ai/workspaces
```

The validation checks:

```text
Hermes /health is reachable.
The shared token works against protected larv-skill endpoints.
The DTT-AI workspace path exists and is readable/writable by this process.
Hermes can complete a test project from that workspace path.
Hermes can record a failed larv skill session.
```

Expected successful result:

```json
{
  "ok": true
}
```

If this fails, fix the reported workspace path, token, URL, or process permissions before connecting the real DTT-AI UI.

## Reference Smoke Client

Start Hermes Core:

```bash
PYTHONPATH=src uvicorn hermes_core.app:app --host 0.0.0.0 --port 8000
```

Run the DTT-AI reference client:

```bash
HERMES_URL=http://127.0.0.1:8000 \
HERMES_DTT_AI_SHARED_TOKEN=<shared-token> \
python3 tools/dtt_ai_larv_skill_smoke.py --mode both
```

If Hermes Core is running without `HERMES_DTT_AI_SHARED_TOKEN`, omit the token environment variable.

The script exercises:

```text
completion flow: session-started -> output -> prompt-shown -> human-answer -> completed
failure flow: session-started -> failed
```

Expected summary:

```json
{
  "flow": "complete",
  "final_state": "project_context_candidate_created"
}
```

```json
{
  "flow": "failed",
  "final_state": "failed",
  "session_status": "recovery_required"
}
```

## DTT-AI Implementation Checklist

```text
[ ] Configure Hermes base URL per environment.
[ ] Configure shared token in both DTT-AI and Hermes Core.
[ ] Generate stable event_id values and reuse them on retries.
[ ] Store Hermes interactive_session.id after session-started.
[ ] Stream output chunks with sequence and stream labels.
[ ] Report prompt-shown before showing or while showing the prompt to the human.
[ ] Pipe the human answer to the actual larv:full runtime.
[ ] Report human-answer after the answer is submitted.
[ ] Report completed only when Hermes can read project_dir.
[ ] Report failed when larv cannot continue.
[ ] Use get_session_status for browser reloads and operator status cards.
[ ] Surface Hermes 400/401/422 errors in DTT-AI operator logs.
```
