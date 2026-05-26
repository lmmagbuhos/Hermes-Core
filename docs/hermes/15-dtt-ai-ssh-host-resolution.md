# DTT-AI SSH Host Resolution Prompt

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

The SSH/tmux runtime spike successfully moved DTT-AI in the correct direction:
- Codex app-server is no longer the active runtime path.
- The active runtime is now `TmuxSshLarvRuntime`.
- The backend probe routes are wired to the SSH/tmux runtime.
- Automated tests prove command construction and route/runtime boundaries.

However, the real runtime is not proven yet because SSH failed before reaching the dev/Contabo server.

Observed blocker:

`ssh: Could not resolve hostname dev: Temporary failure in name resolution`

This means the current DTT-AI backend environment cannot resolve the SSH alias `dev`.

Your next task is to fix or bypass SSH host resolution and then rerun the real SSH/tmux probe.

Do not implement Hermes lifecycle reporting yet.
Do not build the frontend UI yet.
Do not fake a successful runtime.

Goal:
Prove that the DTT-AI backend environment can SSH to the real dev/Contabo server non-interactively and run the real tmux/Codex/larv workflow.

Required checks:
1. Determine which user the DTT-AI backend runs as in this environment.
2. Determine whether that user has an SSH config entry for `dev`.
3. If `dev` is not resolvable, use an explicit SSH target in `LARV_REMOTE_HOST`, such as:
   - `<user>@<server-ip>`
   - `<server-ip>` if SSH user is implied by config
   - a configured host alias that actually resolves from the DTT-AI process user
4. Confirm non-interactive SSH works:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 "$LARV_REMOTE_HOST" 'printf connected'
```

5. Confirm required remote tools:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 "$LARV_REMOTE_HOST" '
  printf "connected\n"
  command -v tmux
  command -v codex
  pwd
'
```

6. Confirm remote write access:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 "$LARV_REMOTE_HOST" '
  mkdir -p "$LARV_REMOTE_BASE_DIR/hermes-runtime-probe" &&
  test -d "$LARV_REMOTE_BASE_DIR/hermes-runtime-probe" &&
  printf "workspace-writable\n"
'
```

7. Confirm Codex can start on the remote server from the DTT-AI-controlled command path.
8. Confirm tmux can create, capture, send keys, and kill a named session.

Use these environment variables:

```bash
LARV_REMOTE_HOST=<resolvable ssh target>
LARV_REMOTE_BASE_DIR=/tmp/dtt-ai-larv-projects
LARV_TMUX_PREFIX=dtt_ai_larv
LARV_CODEX_COMMAND='codex --yolo'
LARV_TRIGGER='/larv:full'
```

If `/larv:full` is not the accepted trigger inside Codex, test `larv:full` and document which one works.

After SSH works, rerun the real runtime probe:
1. Start a project session.
2. Confirm remote project directory is created.
3. Confirm tmux session starts.
4. Confirm `codex --yolo` starts inside tmux.
5. Send the larv trigger.
6. Capture real output.
7. Send one manual answer into the same tmux session.
8. Capture output again and confirm the same session continued.
9. Confirm remote artifact exists:

```bash
test -f '<remote-project-dir>/docs/larv/STATE.yaml'
```

Hard stop:
If SSH cannot connect non-interactively, stop and report the exact missing requirement:
- DNS/host alias missing
- SSH key missing
- SSH user wrong
- known_hosts prompt blocking
- remote command unavailable
- permission denied
- tmux missing
- codex missing
- Codex auth/config missing
- larv skills missing
- workspace path not writable

Deliverables:
1. Exact value used for `LARV_REMOTE_HOST` with secrets redacted.
2. Whether `ssh dev` works from the DTT-AI backend process user.
3. Whether direct host/IP SSH works.
4. Whether non-interactive BatchMode SSH works.
5. Remote paths for `tmux`, `codex`, and the workspace.
6. Logs from the real runtime probe.
7. Evidence that `codex --yolo` started in tmux.
8. Evidence that larv trigger was sent.
9. Evidence that output was captured.
10. Evidence that an answer can be sent into the same tmux session.
11. Evidence that `docs/larv/STATE.yaml` exists remotely.
12. Whether the runtime is now ready to be wrapped with Hermes lifecycle reporting.

Do not proceed to Hermes reporting until the real SSH/tmux runtime has been proven end-to-end.
```

