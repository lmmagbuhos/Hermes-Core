# DTT-AI Runtime Test Report Capture Prompt

Use this prompt inside the DTT-AI project agent before running the browser-driven New Project test.

```text
You are working inside the DTT-AI project.

Before the operator runs the real browser-driven New Project runtime test, add a lightweight test report capture mechanism.

Purpose:
Capture evidence from the actual browser/runtime/Hermes test while the session details are fresh.

Do not change the runtime architecture.
Do not fake report data.
Do not consume Codex quota just to test the report writer.

Recommended report directory:

`docs/runtime-test-reports/`

Recommended filename format:

`YYYY-MM-DD-new-project-browser-test-<sessionId>.md`

If no session ID is available yet, start with:

`YYYY-MM-DD-new-project-browser-test.md`

Report should capture:
1. Test date/time.
2. Browser URL used.
3. Logged-in app user, without password.
4. Whether Hermes was enabled.
5. Hermes URL, with secrets redacted.
6. Runtime environment:
   - `LARV_REMOTE_HOST`
   - `LARV_REMOTE_BASE_DIR`
   - `LARV_TMUX_PREFIX`
   - `LARV_CODEX_COMMAND`
   - `LARV_TRIGGER`
7. Project name.
8. DTT-AI runtime session ID.
9. tmux session name.
10. Remote project directory.
11. Hermes session ID if available.
12. Start response summary.
13. Captured output before first answer.
14. Prompt/question shown to the user.
15. Prompt ID used.
16. Human answer submitted.
17. Captured output after answer.
18. Whether the same tmux/Codex session continued.
19. Artifact evidence:
   - whether `docs/larv/STATE.yaml` exists,
   - any other generated files seen.
20. Hermes status/events if Hermes was enabled:
   - run state,
   - interactive session status,
   - latest event types,
   - project context candidate if created.
21. Errors encountered.
22. Cancel/cleanup result.
23. Final verdict:
   - PASS
   - PARTIAL
   - FAIL
24. Next recommended action.

Implementation options:

Option A: Manual report template only
- Add a Markdown template under `docs/runtime-test-reports/TEMPLATE-new-project-browser-test.md`.
- The operator or agent fills it after testing.
- This is acceptable if it is fastest.

Option B: Backend-assisted report endpoint
- Add an admin-only backend route that writes a report from current session status.
- Example:
  - `POST /api/larv-runtime-probe/:sessionId/report`
- It should collect:
  - local runtime status,
  - captured output,
  - Hermes status if available,
  - artifact check result.
- It can still allow operator notes in the request body.

Recommendation:
Use Option A unless the DTT-AI code already has a simple docs-writing/reporting pattern. Do not overbuild this before the first browser test.

Add this template:

```markdown
# New Project Browser Runtime Test Report

Date:
Verdict: PASS | PARTIAL | FAIL

## Test Setup

- Browser URL:
- App user:
- Hermes enabled:
- Hermes URL:
- Project name:

## Runtime Environment

```text
LARV_REMOTE_HOST=
LARV_REMOTE_BASE_DIR=
LARV_TMUX_PREFIX=
LARV_CODEX_COMMAND=
LARV_TRIGGER=
```

## Session IDs

- DTT-AI session ID:
- tmux session name:
- Remote project directory:
- Hermes session ID:

## Start Result

```json

```

## Output Before Answer

```text

```

## Prompt / Question

- Prompt ID:
- Prompt text:

## Answer Submitted

```text

```

## Output After Answer

```text

```

## Continuation Evidence

- Did the same tmux/Codex session continue:
- Evidence:

## Artifact Evidence

- `docs/larv/STATE.yaml` exists:
- Other files:

## Hermes Evidence

- Hermes run state:
- Hermes interactive session status:
- Latest event types:
- ProjectContextCandidate:

## Errors

```text

```

## Cleanup

- Cancel endpoint called:
- tmux session still active:
- Cleanup notes:

## Next Action

```

Testing:
- No Codex run is required to test the template.
- If you add a backend report endpoint, test it with mocked runtime/Hermes status.

Deliverables:
1. Exact files changed.
2. Whether you implemented Option A or Option B.
3. Where the report/template lives.
4. Any instructions for the operator before running the browser test.
```

