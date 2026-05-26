# DTT-AI Final SSH/tmux Prompt-Answer Proof Prompt

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

The SSH/tmux runtime bridge is now the active runtime direction for Scenario A.

Hermes Core does not need API changes right now. It already has the lifecycle endpoints that DTT-AI will report to after the runtime is fully proven.

Current proven runtime facts:
- The previous Codex app-server path is research-only.
- The active runtime is SSH/tmux.
- Same-server SSH works with `LARV_REMOTE_HOST=localhost`.
- BatchMode SSH works for the `claude-team` process user after authorizing its public key.
- `tmux` exists remotely at `/usr/bin/tmux`.
- `codex` exists and reports `codex-cli 0.131.0`.
- DTT-AI can create the remote project directory.
- DTT-AI can start `codex --yolo` inside tmux.
- DTT-AI can capture tmux pane output.
- DTT-AI can send input into the same tmux session.
- The accepted trigger is `larv:full`, not `/larv:full`.
- Real larv pre-flight ran and created `docs/larv/STATE.yaml`.

Current blocker:
The last fresh rerun was blocked by Codex usage quota:

`You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at 2:04 PM.`

This is not a Hermes blocker.
This is not an SSH blocker.
This is not a tmux blocker.
This is not a runtime architecture blocker.

Your next task:
After Codex quota is available again, run the final SSH/tmux prompt-answer proof.

Do not implement Hermes lifecycle reporting yet.
Do not build the final frontend UI yet.
Do not fake prompt-answer behavior.

Use this same-server configuration:

```bash
LARV_REMOTE_HOST=localhost
LARV_REMOTE_BASE_DIR=/tmp/dtt-ai-larv-projects
LARV_TMUX_PREFIX=dtt_ai_larv
LARV_CODEX_COMMAND='codex --yolo'
LARV_TRIGGER='larv:full'
LARV_SSH_TIMEOUT_MS=60000
LARV_CODEX_READY_TIMEOUT_MS=70000
LARV_CODEX_READY_POLL_INTERVAL_MS=2000
LARV_TMUX_CAPTURE_LINES=900
```

Final proof requirements:
1. Start a fresh runtime probe session.
2. Confirm the remote project directory is created.
3. Confirm tmux session is created.
4. Confirm `codex --yolo` starts inside tmux.
5. Send `larv:full` into the Codex session.
6. Capture real larv output.
7. Let larv reach an actual question or input point.
8. Submit one answer through:
   `POST /api/larv-runtime-probe/:sessionId/answers`
9. Capture output again after the answer.
10. Prove the same tmux session continued after the answer.
11. Confirm `docs/larv/STATE.yaml` exists remotely.
12. If possible, confirm `STATE.yaml` or later larv artifacts advanced after the answer.

Important:
Do not manually type into tmux outside DTT-AI for the answer proof. The answer must go through the DTT-AI backend answer endpoint so we prove the actual product path.

If larv asks multiple questions:
- answer only enough to prove that DTT-AI can resume the same session,
- do not spend quota trying to complete the entire greenfield workflow unless it is cheap and already flowing.

If Codex quota blocks again:
- stop,
- report the quota message,
- do not mark the proof complete.

If Codex asks for directory trust:
- use the existing runtime handling for that prompt,
- document the captured output.

If `larv:full` does not reach a clear prompt:
- report the exact captured output,
- report whether `STATE.yaml` was created,
- report whether the session is still alive,
- do not invent a prompt.

Deliverables:
1. Exact files changed, if any.
2. Test results.
3. Runtime probe command or API calls used.
4. Session ID.
5. tmux session name.
6. Remote project directory.
7. Captured output before answer.
8. The prompt or input point that required a human answer.
9. The answer submitted through the DTT-AI backend endpoint.
10. Captured output after answer.
11. Evidence the same tmux session continued.
12. Evidence `docs/larv/STATE.yaml` exists.
13. Whether the runtime is now ready for Hermes lifecycle reporting.

Success criteria:
The runtime is ready for Hermes wrapping only if this is proven:

`real larv output/question -> DTT-AI backend answer endpoint -> same tmux/Codex session continues`

If that is proven, the next phase is:
wrap the SSH/tmux runtime with Hermes lifecycle reporting.
```

