# DTT-AI Request User Input Resolution Prompt

> **Status: Superseded / research-only.**
>
> This prompt focused on unblocking Codex app-server structured `request_user_input`. That investigation is no longer the primary path for Scenario A.
>
> Current direction: DTT-AI should first prove an SSH/tmux-backed Codex terminal session that mirrors the real manual workflow: `ssh dev`, create the project directory, start `codex --yolo`, invoke `larv:full` inside that Codex session, capture output, and send human answers back into the same persistent session.
>
> Use `14-dtt-ai-ssh-tmux-runtime-spike.md` for the current prompt.

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

The runtime bridge spike successfully proved that Codex app-server can start, `larv:full` is visible, real output streams, and real larv pre-flight artifacts are created.

However, the runtime bridge is not complete because structured prompt handling failed with:

`request_user_input is unavailable in Default mode`

Your next task is to resolve this blocker.

Do not implement Hermes lifecycle reporting yet.
Do not build the New Project frontend yet.
Do not fake prompt-answer behavior.

Goal:
Determine whether Codex app-server can run `larv:full` in a mode where `request_user_input` is available, or prove that it cannot.

Investigate:
1. What Codex runtime mode enables `request_user_input`?
2. Is there a Plan mode or interactive mode parameter in Codex app-server `thread/start`, `turn/start`, or tool configuration?
3. Does Codex app-server expose `request_user_input` only under certain tool permissions?
4. Can the app-server session be initialized with a mode/profile/toolset that includes `request_user_input`?
5. Is this limitation coming from the Codex CLI, the app-server protocol, the model mode, or the skill invocation context?
6. Is there a documented or schema-visible way to respond to server tool requests from app-server?
7. Can a minimal non-larv prompt intentionally trigger `request_user_input` in the same app-server mode?

Required experiment:
1. Start Codex app-server.
2. Start a thread in the same way as the larv spike.
3. Run a minimal instruction that should ask for human input using `request_user_input`.
4. Try all reasonable mode/tool/session parameters discoverable in schema or local Codex config.
5. Record which modes are accepted and which fail.

If `request_user_input` can be enabled:
1. Update `codexAppServerRuntime.ts` to use the correct mode/config.
2. Prove one real `larv:full` prompt appears as a structured prompt.
3. Prove `submitAnswer(sessionId, promptId, answer)` answers the same runtime request.

If `request_user_input` cannot be enabled:
1. Implement and prove the fallback model:
   - detect larv questions from assistant text/output,
   - mark the runtime session as waiting for input,
   - accept an answer through `submitAnswer`,
   - continue the same Codex thread with a later `turn/start` containing the answer,
   - prove the same larv workflow continues after the answer.
2. This fallback must still use the real Codex thread and real `larv:full`; do not simulate the workflow.

Deliverables:
1. Root cause of `request_user_input is unavailable in Default mode`.
2. Whether there is a working mode/config to enable it.
3. If yes, logs from one real structured prompt-answer cycle.
4. If no, logs from one real fallback prompt-answer continuation cycle.
5. Exact files changed.
6. Test results.
7. Whether the runtime bridge is now ready for Hermes lifecycle reporting.
```
