# DTT-AI New Project Page Prompt

Use this prompt inside the DTT-AI project agent.

```text
You are working inside the DTT-AI project.

The DTT-AI backend now has:
- a proven SSH/tmux runtime for `codex --yolo -> larv:full`,
- backend answer submission into the same tmux/Codex session,
- Hermes lifecycle reporting through `HermesReportingLarvRuntime`,
- opt-in Hermes reporting via `HERMES_ENABLED=true`.

Your next task is to add the frontend/operator workflow for Scenario A.

Build a separate “New Project” tab/page.

Do not modify or replace the existing chat flow.
Do not force the larv workflow into the support-ticket chat UI.
Do not build a fake demo.
Use the existing backend runtime/probe routes that talk to the real SSH/tmux runtime.

Goal:
Prove the DTT-AI operator loop in the actual website:

`create project -> see real larv output -> answer prompt -> see same session continue -> inspect status`

Recommended UI shape:
- Add sidebar item: `New Project`
- Add route/page: `/new-project`
- Page components:
  - project name input
  - start button
  - runtime status card
  - terminal-style output panel
  - prompt/answer panel
  - cancel button
  - Hermes status panel when Hermes reporting is enabled

Backend routes already available from the runtime probe:
- `POST /api/larv-runtime-probe/start`
- `GET /api/larv-runtime-probe/:sessionId/output`
- `POST /api/larv-runtime-probe/:sessionId/answers`
- `GET /api/larv-runtime-probe/:sessionId/status`
- `POST /api/larv-runtime-probe/:sessionId/cancel`

If route names changed during backend work, inspect the actual DTT-AI backend routes and use the real names.

Implementation guidance:
1. Add the new route/page without disturbing existing chat.
2. Add a sidebar/nav entry for `New Project`.
3. Use the existing app layout/styles/components where possible.
4. Keep the first version operational and clear, not overdesigned.
5. Poll backend status/output first unless SSE already exists cleanly in the repo.
6. If you add SSE, keep it small and testable; do not block the page on SSE.
7. Preserve admin/auth behavior already applied to the backend probe routes.

Frontend behavior:
1. User enters project name.
2. User clicks Start.
3. Frontend calls backend start route.
4. Store returned DTT-AI session ID.
5. Poll output/status for that session.
6. Show terminal output in chronological order.
7. When a prompt/input point is available, show answer input.
8. User submits answer.
9. Frontend calls answer route.
10. Continue polling and show new output.
11. User can cancel the session.
12. If Hermes status is available, show Hermes run state and Hermes session ID.

Prompt handling:
For this first UI pass, do not overbuild prompt parsing.

Acceptable:
- show latest captured output,
- provide a manual answer box when session is running or waiting,
- let the user submit an answer with a prompt ID.

Better if already available:
- use backend-detected prompt records.

Do not fake a prompt.

Suggested prompt ID fallback:
If backend does not provide a structured prompt ID yet, generate a stable UI prompt ID like:

`manual-prompt-<sessionId>-<counter>`

Testing:
Add frontend tests for:
1. page renders project form,
2. start button calls backend start route,
3. output/status polling renders terminal output,
4. answer submit calls backend answer route,
5. cancel calls backend cancel route,
6. existing chat route/page still works or is not modified.

Add backend route/client tests only if the page needs a new frontend API wrapper.

Manual verification:
1. Start Hermes Core if testing Hermes reporting:

```bash
PYTHONPATH=src HERMES_DTT_AI_SHARED_TOKEN=<shared-token> uvicorn hermes_core.app:app --host 0.0.0.0 --port 8000
```

2. Start DTT-AI with:

```bash
HERMES_ENABLED=true
HERMES_URL=http://127.0.0.1:8000
HERMES_DTT_AI_SHARED_TOKEN=<shared-token>
LARV_REMOTE_HOST=localhost
LARV_REMOTE_BASE_DIR=/tmp/dtt-ai-larv-projects
LARV_TMUX_PREFIX=dtt_ai_larv
LARV_CODEX_COMMAND='codex --yolo'
LARV_TRIGGER='larv:full'
```

3. Open the DTT-AI website.
4. Navigate to `New Project`.
5. Start a project.
6. Confirm real output appears.
7. Submit one answer through the UI.
8. Confirm output continues in the same session.
9. Confirm Hermes status is visible when enabled.

Deliverables:
1. Exact files changed.
2. Route/page path added.
3. Sidebar/nav change.
4. Tests run and results.
5. Screenshots or textual UI verification.
6. Whether polling or SSE was used.
7. Whether Hermes status displays.
8. Any remaining UX/runtime blockers.

Success criteria:
The existing chat remains undisturbed, and the new `New Project` page can drive the proven backend SSH/tmux larv runtime from the browser.
```

