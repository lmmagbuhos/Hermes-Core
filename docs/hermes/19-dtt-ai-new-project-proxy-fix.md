# DTT-AI New Project Proxy Fix Prompt

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

The New Project page exists, but browser runtime testing is blocked by a frontend/backend proxy mismatch.

This is not a Hermes Core blocker.
This is not an SSH/tmux runtime blocker.
This is not a larv blocker.

Observed browser URL:

`http://31.220.79.31:5174/new-project`

Observed UI behavior:
1. Login works with the temporary admin app user.
2. User enters a project name.
3. User clicks Start.
4. UI shows:

`Request failed: 404`

Direct backend reproduction:

```bash
curl -X POST http://127.0.0.1:3001/api/larv-runtime-probe/start \
  -H 'Content-Type: application/json' \
  --data '{"projectName":"DocsCheck","workspaceDir":"/tmp/dtt-ai-larv-projects/docs-check"}'
```

Response:

```json
{
  "statusCode": 404,
  "path": "/api/larv-runtime-probe/start",
  "errors": {
    "message": "Cannot POST /api/larv-runtime-probe/start",
    "name": "NotFoundException"
  }
}
```

Root cause:
Port `3001` is currently serving a different Node/Nest service, not the isolated DTT-AI `apps/ai-service` process that contains the larv runtime probe route.

The Vite frontend proxy sends `/api/...` calls to `http://localhost:3001`, so the New Project page is reaching the wrong backend.

Your task:
Fix the dev-server wiring so the New Project page calls the correct isolated DTT-AI `apps/ai-service` backend.

Do not modify Hermes Core.
Do not change the SSH/tmux runtime logic unless route wiring proves it is actually wrong.
Do not continue runtime UI validation until the route reaches the correct backend.

Valid fix options:

Option A:
Start the correct isolated `apps/ai-service` on port `3001`, if that port can be freed safely.

Option B:
Start the correct isolated `apps/ai-service` on another port and update the frontend Vite proxy target to that port.

Choose the safer option for this worktree. Do not kill unrelated production services unless explicitly approved.

Required checks:
1. Identify which process is currently listening on `3001`.
2. Identify which port the isolated worktree `apps/ai-service` should use.
3. Confirm the isolated `apps/ai-service` process has the larv runtime probe route mounted:

`POST /api/larv-runtime-probe/start`

4. Confirm direct curl reaches the correct backend and no longer returns the Nest `Cannot POST` 404.

Example direct check:

```bash
curl -X POST http://127.0.0.1:<correct-ai-service-port>/api/larv-runtime-probe/start \
  -H 'Content-Type: application/json' \
  --data '{"projectName":"DocsCheck","workspaceDir":"/tmp/dtt-ai-larv-projects/docs-check"}'
```

It is acceptable if this starts a real runtime session, but be mindful of Codex quota. If needed, add or use a health/test route to prove routing without consuming quota. Do not fake success for the actual start route.

5. Confirm the frontend dev server proxies `/api/larv-runtime-probe/start` to the same correct backend port.
6. Confirm the browser New Project Start button no longer returns the Nest 404.

Runtime environment for the correct DTT-AI backend:

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

If Hermes reporting is enabled:

```bash
HERMES_ENABLED=true
HERMES_URL=http://127.0.0.1:8000
HERMES_DTT_AI_SHARED_TOKEN=<shared-token>
```

Frontend dev server note:
When using a laptop/external browser, do not use `127.0.0.1` as the browser URL. Use:

`http://31.220.79.31:5174/new-project`

But server-side proxy targets can still use `localhost` because they run on the server.

Deliverables:
1. Which process was on port `3001`.
2. Which option you chose: use port `3001` or change proxy target.
3. Exact files changed.
4. Exact commands used to start the correct backend and frontend.
5. Curl result proving the correct backend route is reachable.
6. Browser result proving the New Project Start button no longer hits the wrong Nest backend.
7. Whether any real Codex/tmux session was started during verification.
8. Any tmux sessions created and whether they were cleaned up.

Success criteria:
The New Project page’s `/api/larv-runtime-probe/start` request reaches the isolated DTT-AI `apps/ai-service` backend that owns the SSH/tmux runtime route.
```

