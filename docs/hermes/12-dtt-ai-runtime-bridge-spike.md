# DTT-AI Runtime Bridge Spike Prompt

> **Status: Superseded / research-only.**
>
> This prompt explored Codex app-server as the first runtime bridge candidate. That was useful research, but the current preferred direction is now the SSH/tmux-backed Codex terminal workflow described in `14-dtt-ai-ssh-tmux-runtime-spike.md`.
>
> Reason: the real manual workflow is `ssh dev -> mkdir project -> codex --yolo -> invoke larv:full inside the Codex session -> answer prompts in that same session`. The app-server spike hit `request_user_input is unavailable in Default mode`, while the SSH/tmux direction matches the proven human workflow and does not require structured app-server prompt events.

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

DTT-AI’s current repo does not yet have the runtime bridge required to invoke a real long-running `larv:full` session. Hermes Core is ready enough for Scenario A, but DTT-AI still needs the live runtime layer that produces real output, prompt, answer, completion, and failure events.

Your next task is not Hermes integration and not the full frontend UI.

Your next task is a backend-only Codex app-server runtime bridge spike for `larv:full`.

Do not build the frontend yet.
Do not connect Hermes yet except through placeholder interfaces.
Do not fake `larv:full`.
Do not simulate prompts or generated artifacts.

Goal:
Prove DTT-AI can start a real `larv:full` session, observe output, surface one human prompt, submit an answer, and detect completion/failure.

Recommended files:
- `apps/ai-service/src/services/larvRuntime/types.ts`
- `apps/ai-service/src/services/larvRuntime/codexAppServerRuntime.ts`
- `apps/ai-service/src/routes/larvRuntimeProbe.ts`

Runtime interface:
- `startLarvFull({ projectName, workspaceDir })`
- `submitAnswer(sessionId, promptId, answer)`
- `getStatus(sessionId)`
- `cancel(sessionId)`

Implementation direction:
Use Codex app-server as the first runtime candidate.

Why:
- It is closer to the actual agent/skill runtime than shell/PTY scraping.
- It may expose structured notifications.
- It may support human input requests cleanly.
- It avoids pretending `larv:full` is a CLI command.

Known Codex app-server capabilities to investigate:
- `thread/start`
- `turn/start`
- `turn/steer`
- streamed notifications such as `item/agentMessage/delta`
- completion notifications such as `turn/completed`
- human prompt requests such as `item/tool/requestUserInput`

Relevant generated schema may exist under:
`/tmp/codex-app-schema`

Check types such as:
- `ThreadStartParams`
- `TurnStartParams`
- `ToolRequestUserInputParams`

The spike must verify:
1. Codex app-server can start from the DTT-AI backend environment.
2. `larv:full` skill is visible.
3. A thread can start with `cwd = scratch workspace`.
4. A turn can start with an explicit instruction to run real `larv:full`.
5. Output can be streamed or collected incrementally.
6. Prompt/input requests can be detected.
7. A human answer can be sent back into the same session/thread.
8. Completion/failure can be detected.
9. A real project directory/artifact path exists after completion.

If `request_user_input` events are emitted:
- map them to pending DTT-AI prompts,
- store `prompt_id`,
- allow `submitAnswer(sessionId, promptId, answer)` to answer the same runtime request.

If `request_user_input` events are not emitted:
- determine whether `larv:full` asks questions as normal assistant text,
- document whether continuation turns can answer those questions in the same Codex thread,
- do not mark the bridge solved until one real prompt-answer cycle is proven.

Expected route for the spike:
- Add a backend-only probe route, for example:
  - `POST /api/larv-runtime-probe/start`
  - `POST /api/larv-runtime-probe/:sessionId/answers`
  - `GET /api/larv-runtime-probe/:sessionId/status`

The route can be ugly and internal-only for the spike. It does not need production UI polish.

The route must not fake events. It must expose what the real runtime produces.

Session registry:
- In-memory is acceptable for the spike.
- Before production, use persistent storage because the current DigitalOcean service can restart.

Important deployment constraints:
- Current deployed DTT-AI appears to be a single DigitalOcean web service.
- Long-running agent sessions require Codex auth/config/skills to exist in that environment.
- The deployment must permit long-lived child processes or a persistent app-server connection.
- If those conditions are not true, report that as a blocker.

Fallback:
Do not use raw PTY/TUI scraping unless Codex app-server fails.

Raw PTY/tmux/screen is a fallback only because it is more brittle and harder to recover after restarts. If Codex app-server fails, document exactly why before proposing PTY fallback.

Deliverables:
1. Where the runtime bridge lives in DTT-AI.
2. Whether Codex app-server is viable.
3. Exact commands used to start the probe.
4. Logs from one real run or the precise failure preventing one.
5. Whether `larv:full` appears as an available skill.
6. Whether a prompt can be surfaced and answered.
7. Whether generated artifacts exist after completion.
8. Blockers and required environment changes.
9. A recommendation: proceed with Codex app-server, fall back to PTY, or pause because the runtime cannot be invoked from DTT-AI.

Do not implement Hermes HTTP reporting yet.

Only after this runtime spike proves a real `larv:full` prompt-answer-completion cycle should DTT-AI proceed to:
1. Wrap the runtime with Hermes lifecycle reporting.
2. Add backend larv session routes.
3. Add SSE/live browser streaming.
4. Add the New Project frontend page.
5. Connect final completion to Hermes Core.
```
