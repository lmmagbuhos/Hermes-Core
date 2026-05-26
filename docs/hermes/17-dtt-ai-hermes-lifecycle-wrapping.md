# DTT-AI Hermes Lifecycle Wrapping Prompt

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

The SSH/tmux runtime bridge is now proven for Scenario A.

Proven runtime boundary:

`real larv output/question -> DTT-AI backend answer endpoint -> same tmux/Codex session continues`

Do not revisit Codex app-server for this phase.
Do not rebuild the runtime from scratch.
Do not build the final frontend UI yet.
Do not fake Hermes events.

Your task:
Wrap the proven `TmuxSshLarvRuntime` with Hermes Core lifecycle reporting.

Hermes Core is ready and already exposes the required API:
- `POST /workflows/new-project/larv-skill/session-started`
- `POST /workflows/new-project/larv-skill/{session_id}/output`
- `POST /workflows/new-project/larv-skill/{session_id}/prompt-shown`
- `POST /workflows/new-project/larv-skill/{session_id}/human-answer`
- `POST /workflows/new-project/larv-skill/{session_id}/completed`
- `POST /workflows/new-project/larv-skill/{session_id}/failed`
- `GET /workflows/new-project/larv-skill/{session_id}/status`

Hermes Core docs to reference:
- `docs/hermes/11-dtt-ai-handoff.md`
- `docs/hermes/10-dtt-ai-larv-skill-contract.md`

Runtime facts to preserve:
- `LARV_REMOTE_HOST=localhost` works for same-server testing.
- `LARV_TRIGGER='larv:full'` is correct.
- `/larv:full` is not accepted in this Codex TUI.
- `codex --yolo` runs inside tmux.
- DTT-AI can send answers into the same tmux session.

Add DTT-AI config:
- `HERMES_URL`
- `HERMES_DTT_AI_SHARED_TOKEN`
- optional `HERMES_ENABLED`

Recommended files:
- `apps/ai-service/src/services/hermes/hermesClient.ts`
- `apps/ai-service/src/services/hermes/hermesClient.test.ts`
- `apps/ai-service/src/services/larvRuntime/hermesReportingLarvRuntime.ts`
- `apps/ai-service/src/services/larvRuntime/hermesReportingLarvRuntime.test.ts`
- update `apps/ai-service/src/routes/larvRuntimeProbe.ts`
- update shared validation/env schemas if the repo has a standard place for them

Hermes client responsibilities:
1. Send `X-Hermes-Token` when configured.
2. Generate stable `event_id` values.
3. Implement typed methods:
   - `startSession`
   - `recordOutput`
   - `recordPromptShown`
   - `recordHumanAnswer`
   - `completeSession`
   - `failSession`
   - `getStatus`
4. Preserve Hermes structured errors:
   - `detail.code`
   - `detail.message`
   - `detail.path`
5. Log enough context for operator debugging.

Event ID rules:
Use stable IDs based on the DTT-AI runtime session ID:
- `<dtt-session-id>-started`
- `<dtt-session-id>-output-000001`
- `<dtt-session-id>-prompt-<prompt-id>`
- `<dtt-session-id>-answer-<prompt-id>`
- `<dtt-session-id>-completed`
- `<dtt-session-id>-failed`

Do not generate a new event ID when retrying the same event.

Wrapper behavior:

1. On runtime start:
   - start the real SSH/tmux runtime first,
   - then call Hermes `session-started`,
   - store Hermes `interactive_session.id` alongside the DTT-AI runtime session.

2. On output capture:
   - detect only newly captured output chunks,
   - increment sequence numbers,
   - call Hermes `output`.

3. On prompt detection/manual prompt registration:
   - call Hermes `prompt-shown`,
   - include `prompt_id`, prompt text, choices/default when known, and metadata.

4. On answer submission:
   - send answer to the real tmux/Codex session first,
   - only after that succeeds, call Hermes `human-answer`.

5. On cancel or runtime failure:
   - call Hermes `failed` with a useful reason.

6. On completion:
   - verify the remote project directory/artifact path is readable by Hermes Core under the current same-server assumption,
   - call Hermes `completed`.

Important ordering rule:
Hermes should reflect real runtime actions. Do not report success to Hermes before the real runtime action succeeds.

For example:
`send answer into tmux -> then report human-answer to Hermes`

Do not call Hermes `completed` unless real artifacts exist.

Status:
Expose a route or extend the existing probe status so DTT-AI can show:
- local runtime status,
- tmux session name,
- remote project directory,
- Hermes session ID,
- Hermes run state from `GET /status`,
- latest Hermes candidate info when available.

Testing:
Add unit tests with mocked Hermes HTTP calls proving:
1. `session-started` is called after runtime start.
2. output chunks are sent with stable sequence/event IDs.
3. prompt-shown is sent for detected/manual prompts.
4. answer is sent to runtime before Hermes `human-answer`.
5. runtime failure/cancel calls Hermes `failed`.
6. completion calls Hermes `completed` only when artifact path is present.
7. Hermes structured errors are preserved/logged.

Do not require a real Codex quota-consuming run for unit tests. Use mocks for Hermes client and runtime in tests.

Manual verification:
After unit tests pass, run a short real probe only if Codex quota is available:
1. Start Hermes Core.
2. Run Hermes environment validation.
3. Start DTT-AI runtime probe.
4. Confirm Hermes receives `session-started`.
5. Capture output and confirm Hermes receives `output`.
6. Submit one answer and confirm Hermes receives `human-answer`.
7. If completion is not reached cheaply, do not force a full larv run just for this phase.

Deliverables:
1. Exact files changed.
2. Test results.
3. Whether Hermes reporting is behind `HERMES_ENABLED`.
4. Example environment variables.
5. Sample Hermes request logs or mocked request evidence.
6. Whether the backend is ready for SSE/frontend New Project page.

Success criteria:
The proven SSH/tmux runtime emits truthful Hermes lifecycle events without changing the runtime behavior.
```

