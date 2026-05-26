# DTT-AI SSH/tmux Runtime Spike Prompt

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

Context:
DTT-AI and Hermes Core are separate projects.

Hermes Core is already ready enough for Scenario A reporting. It can receive:
- session-started
- output
- prompt-shown
- human-answer
- completed
- failed
- status

But DTT-AI still needs the real runtime bridge that produces those events.

Important correction:
The preferred runtime direction is no longer Codex app-server.

Codex app-server was investigated and successfully proved that `larv:full` is visible and real larv pre-flight artifacts can be created, but it hit this blocker:

`request_user_input is unavailable in Default mode`

Keep the Codex app-server files as research for now, but do not continue building on that path for Scenario A unless SSH/tmux fails.

Current source of truth:
DTT-AI should automate the real manual workflow:

1. SSH into the dev/Contabo server.
2. Create a directory for the new project.
3. `cd` into that directory.
4. Start a persistent Codex session with `codex --yolo`.
5. Invoke the `larv:full` skill inside that Codex session.
6. Stream/display the Codex session output.
7. When larv asks a question, let the human answer in DTT-AI.
8. Send the human answer back into the same persistent Codex session.
9. Continue until artifacts are generated or the session fails.

Do not type `larv:full` into a plain shell and pretend it is an OS command.
`larv:full` is a Codex skill trigger. The session must be a real Codex session.

Recommended runtime strategy:
Use SSH + tmux.

Why tmux:
- It mirrors the real manual server workflow.
- It keeps the session alive if the browser disconnects.
- It gives DTT-AI a stable session name to reconnect to.
- DTT-AI can capture pane output.
- DTT-AI can send answers back into the same running session.
- It avoids the Codex app-server `request_user_input` blocker.

Cleanup requirement:
Before implementing the SSH/tmux spike, clean up or quarantine the previous Codex app-server runtime spike work so the codebase direction is not ambiguous.

Do one of these:
1. Remove the Codex app-server probe files if they are not needed.
2. Or move/mark them clearly as research-only and unused by the active runtime path.

Previous spike files that may need cleanup:
- `apps/ai-service/src/services/larvRuntime/codexAppServerRuntime.ts`
- `apps/ai-service/src/services/larvRuntime/codexAppServerRuntime.test.ts`
- `apps/ai-service/src/routes/larvRuntimeProbe.ts`
- `apps/ai-service/src/routes/larvRuntimeProbe.test.ts`
- any route mounting added only for the app-server probe

Do not leave DTT-AI with two competing runtime implementations unless one is clearly disabled/research-only.

New implementation target:
Build a backend-only SSH/tmux runtime spike.

Recommended files:
- `apps/ai-service/src/services/larvRuntime/types.ts`
- `apps/ai-service/src/services/larvRuntime/tmuxSshLarvRuntime.ts`
- `apps/ai-service/src/services/larvRuntime/tmuxSshLarvRuntime.test.ts`
- `apps/ai-service/src/routes/larvRuntimeProbe.ts`
- `apps/ai-service/src/routes/larvRuntimeProbe.test.ts`

If `types.ts` already exists from the previous spike, reuse it if the interface still fits. Otherwise update it for the tmux model.

Runtime interface:
- `startLarvFull({ projectName, workspaceDir })`
- `captureOutput(sessionId)`
- `submitAnswer(sessionId, promptId, answer)`
- `getStatus(sessionId)`
- `cancel(sessionId)`

The runtime should store:
- DTT-AI session ID
- remote tmux session name
- remote project directory
- output sequence number
- last captured output
- status: starting | running | waiting_for_input | completed | failed | cancelled

SSH/tmux flow to prove:
1. Connect to the configured dev server.
2. Create the remote project directory.
3. Start a named tmux session in that directory.
4. Run `codex --yolo` inside that tmux session.
5. Send the larv trigger into the Codex session.
6. Capture pane output.
7. Detect that real larv output is appearing.
8. Send one human answer into the same tmux session.
9. Capture output again and prove the same session continued.
10. Confirm `docs/larv/STATE.yaml` exists in the remote project directory.

The larv trigger should match what the real Codex session accepts.
Try `/larv:full` first if that is the real slash-style trigger.
If the actual accepted input is `larv:full`, document that evidence and use it.

Configuration:
Add or use environment variables like:
- `LARV_REMOTE_HOST=dev`
- `LARV_REMOTE_BASE_DIR=/path/where/dtt-ai/creates/projects`
- `LARV_TMUX_PREFIX=dtt_ai_larv`
- `LARV_CODEX_COMMAND=codex --yolo`
- `LARV_TRIGGER=/larv:full`

Do not hardcode server paths or credentials in source code.

Probe routes:
Keep the probe backend-only and admin-protected.

Suggested routes:
- `POST /api/larv-runtime-probe/start`
- `GET /api/larv-runtime-probe/:sessionId/output`
- `POST /api/larv-runtime-probe/:sessionId/answers`
- `GET /api/larv-runtime-probe/:sessionId/status`
- `POST /api/larv-runtime-probe/:sessionId/cancel`

The probe does not need the final frontend UI.

The probe must not fake:
- larv output
- prompts
- answers
- completion
- generated artifacts

Prompt detection:
For this spike, prompt detection can be simple.

Acceptable first version:
- capture tmux output,
- show it as raw text,
- allow the operator/tester to submit an answer manually.

Do not block the spike on perfect prompt parsing.

The critical proof is that DTT-AI can send an answer back into the same persistent Codex/tmux session and larv continues.

Completion detection:
For this spike, do not overbuild completion detection.

At minimum, prove:
- tmux session exists,
- output is captured,
- `docs/larv/STATE.yaml` exists after larv starts,
- session can receive answers.

If you can detect final completion reliably from output or generated files, document how.

Hermes integration:
Do not implement Hermes lifecycle reporting yet.

Only after this SSH/tmux spike proves real session start, output capture, answer submission, and artifact presence should DTT-AI wire Hermes calls around the runtime.

Deliverables:
1. Exact files changed.
2. Whether previous Codex app-server spike files were removed or marked research-only.
3. Exact SSH/tmux commands used under the hood.
4. Exact environment variables required.
5. Test results.
6. Logs/output from one real run.
7. Evidence that the remote project directory was created.
8. Evidence that `codex --yolo` started in tmux.
9. Evidence that `larv:full` was invoked inside Codex.
10. Evidence that output was captured.
11. Evidence that an answer can be sent into the same session.
12. Evidence that `docs/larv/STATE.yaml` exists.
13. Whether this runtime is ready to be wrapped with Hermes lifecycle reporting.

Hard stop:
If DTT-AI cannot SSH to the dev server, cannot start tmux, cannot start Codex, or cannot send input back into the same session, stop and report the exact blocker. Do not build Hermes reporting or frontend UI around an unproven runtime.
```

