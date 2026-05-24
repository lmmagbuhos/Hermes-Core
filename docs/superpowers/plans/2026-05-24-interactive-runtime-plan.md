# Interactive Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the existing PTY runner, interactive session records, and new-project workflow so Hermes can start a real interactive command, read terminal output, persist transcripts, detect waiting prompts, write human answers to stdin, and mark interrupted/completed sessions correctly.

**Architecture:** Add an in-process `InteractiveRuntime` that owns live PTY processes by `session_id`, while durable session metadata remains in SQLite through `InteractiveSessionService`. The runtime is intentionally process-local for this slice; if the server restarts, Hermes reports the session as interrupted/recovery-required instead of pretending the PTY is still alive. API and CLI commands expose read/input/status operations that DTT-AI can later call.

**Tech Stack:** Python 3.12, FastAPI, Typer, SQLAlchemy 2, pytest, Ruff, standard-library PTY/process APIs, local transcript files.

---

## Scope

Implemented:

```text
in-process session-to-PTY registry
start live interactive command from workflow service
persist process_id to InteractiveSessionRecord
read terminal output by session_id
append transcript chunks to transcript_ref
simple prompt detection
write human input to live PTY stdin
mark session completed when process exits
mark recovery_required when DB session exists but live PTY is gone
API and CLI access for runtime read/status/input
```

Deferred:

```text
distributed worker process registry
WebSocket/SSE terminal streaming
durable PTY recovery after server restart
real DTT-AI browser UI
automatic larv:full artifact completion trigger
```

## Target File Structure

```text
src/hermes_core/execution/interactive.py
src/hermes_core/runtime/__init__.py
src/hermes_core/runtime/interactive.py
src/hermes_core/sessions/service.py
src/hermes_core/workflows/new_project.py
src/hermes_core/api/routes.py
src/hermes_core/cli.py
tests/test_interactive_runtime.py
tests/test_api_interactive_runtime.py
tests/test_cli_interactive_runtime.py
```

## Task 1: Extend Session Service for Runtime State

**Files:**
- Modify: `src/hermes_core/sessions/service.py`
- Create: `tests/test_interactive_runtime.py`

- [ ] **Step 1: Write failing tests for process and transcript state**

Create `tests/test_interactive_runtime.py`:

```python
from hermes_core.db import create_session_factory, init_db
from hermes_core.sessions.service import InteractiveSessionService


def test_session_service_sets_process_id_and_appends_transcript(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    transcript = tmp_path / "transcript.log"
    service = InteractiveSessionService(session_factory)
    session = service.create(
        run_id=1,
        command=["python3"],
        cwd=str(tmp_path),
        transcript_ref=str(transcript),
    )

    with_process = service.set_process_id(session.id, process_id=1234)
    assert with_process.process_id == 1234

    updated = service.append_transcript(session.id, "Project name? ")
    assert updated.status == "running"
    assert transcript.read_text(encoding="utf-8") == "Project name? "


def test_session_service_marks_completed_and_recovery_required(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = InteractiveSessionService(session_factory)
    session = service.create(
        run_id=1,
        command=["python3"],
        cwd=str(tmp_path),
        transcript_ref=str(tmp_path / "transcript.log"),
    )

    completed = service.mark_completed(session.id)
    assert completed.status == "completed"

    recovery = service.mark_recovery_required(session.id)
    assert recovery.status == "recovery_required"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_interactive_runtime.py -v
```

Expected:

```text
AttributeError: 'InteractiveSessionService' object has no attribute 'set_process_id'
```

- [ ] **Step 3: Implement runtime state methods**

Modify `src/hermes_core/sessions/service.py` by adding:

```python
from pathlib import Path
```

Add methods to `InteractiveSessionService`:

```python
    def set_process_id(self, session_id: str, *, process_id: int) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            record.process_id = process_id
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def append_transcript(self, session_id: str, chunk: str) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            transcript_path = Path(record.transcript_ref)
            transcript_path.parent.mkdir(parents=True, exist_ok=True)
            with transcript_path.open("a", encoding="utf-8") as handle:
                handle.write(chunk)
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def mark_completed(self, session_id: str) -> InteractiveSessionRecord:
        return self._set_status(session_id, "completed")

    def mark_recovery_required(self, session_id: str) -> InteractiveSessionRecord:
        return self._set_status(session_id, "recovery_required")

    def _set_status(self, session_id: str, status: str) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            record.status = status
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
```

- [ ] **Step 4: Verify session runtime-state tests pass**

Run:

```bash
pytest tests/test_interactive_runtime.py -v
```

Expected:

```text
2 passed
```

## Task 2: Implement Interactive Runtime Registry

**Files:**
- Create: `src/hermes_core/runtime/__init__.py`
- Create: `src/hermes_core/runtime/interactive.py`
- Modify: `tests/test_interactive_runtime.py`

- [ ] **Step 1: Add runtime tests**

Append to `tests/test_interactive_runtime.py`:

```python
from hermes_core.runtime.interactive import InteractiveRuntime


def test_runtime_starts_reads_writes_and_completes_process(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    script = tmp_path / "ask.py"
    script.write_text(
        "answer = input('Project name? ')\nprint(f'created:{answer}')\n",
        encoding="utf-8",
    )

    runtime = InteractiveRuntime(session_factory)
    session = runtime.start(
        run_id=1,
        command=["python3", str(script)],
        cwd=str(tmp_path),
        transcript_ref=str(tmp_path / "transcript.log"),
    )

    first = runtime.read(session.id, timeout=2)
    assert "Project name?" in first.output
    assert first.status == "waiting_for_input"

    runtime.write_input(session.id, "AeroTrack\n", prompt_id=first.prompt_id)
    second = runtime.read(session.id, timeout=5)

    assert "created:AeroTrack" in second.output
    assert second.status == "completed"
    assert "created:AeroTrack" in (tmp_path / "transcript.log").read_text(encoding="utf-8")


def test_runtime_marks_recovery_required_when_process_missing(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = InteractiveSessionService(session_factory)
    session = service.create(
        run_id=1,
        command=["python3"],
        cwd=str(tmp_path),
        transcript_ref=str(tmp_path / "transcript.log"),
    )

    runtime = InteractiveRuntime(session_factory)
    status = runtime.status(session.id)

    assert status.status == "recovery_required"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_interactive_runtime.py::test_runtime_starts_reads_writes_and_completes_process -v
```

Expected:

```text
ModuleNotFoundError: No module named 'hermes_core.runtime'
```

- [ ] **Step 3: Create runtime package**

Create `src/hermes_core/runtime/__init__.py`:

```python
"""Live runtime registries for active Hermes execution sessions."""
```

- [ ] **Step 4: Implement interactive runtime**

Create `src/hermes_core/runtime/interactive.py`:

```python
from dataclasses import dataclass
from hashlib import sha1

from sqlalchemy.orm import Session, sessionmaker

from hermes_core.execution.contracts import PtyProcess
from hermes_core.execution.interactive import PtyInteractiveRunner
from hermes_core.models import InteractiveSessionRecord
from hermes_core.sessions.service import InteractiveSessionService


@dataclass(frozen=True)
class RuntimeReadResult:
    session_id: str
    output: str
    status: str
    prompt_id: str | None


@dataclass(frozen=True)
class RuntimeStatus:
    session_id: str
    status: str
    process_id: int | None


class InteractiveRuntime:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        runner: PtyInteractiveRunner | None = None,
    ):
        self.session_factory = session_factory
        self.sessions = InteractiveSessionService(session_factory)
        self.runner = runner or PtyInteractiveRunner()
        self._processes: dict[str, PtyProcess] = {}

    def start(
        self,
        *,
        run_id: int,
        command: list[str],
        cwd: str,
        transcript_ref: str,
    ) -> InteractiveSessionRecord:
        process = self.runner.start(command, cwd)
        session = self.sessions.create(
            run_id=run_id,
            command=command,
            cwd=cwd,
            transcript_ref=transcript_ref,
            process_id=process.pid,
        )
        self._processes[session.id] = process
        return session

    def read(self, session_id: str, *, timeout: float = 0.2) -> RuntimeReadResult:
        process = self._processes.get(session_id)
        if process is None:
            session = self.sessions.mark_recovery_required(session_id)
            return RuntimeReadResult(session.id, output="", status=session.status, prompt_id=None)

        output = self.runner.read_available(process, timeout=timeout)
        if output:
            self.sessions.append_transcript(session_id, output)

        exit_code = self.runner.poll(process)
        if exit_code is not None:
            session = self.sessions.mark_completed(session_id)
            self._processes.pop(session_id, None)
            return RuntimeReadResult(session.id, output=output, status=session.status, prompt_id=None)

        prompt_id = self._detect_prompt_id(output)
        if prompt_id:
            session = self.sessions.mark_waiting_for_input(
                session_id,
                prompt=output.strip(),
                prompt_id=prompt_id,
            )
            return RuntimeReadResult(session.id, output=output, status=session.status, prompt_id=prompt_id)

        session = self.sessions.get(session_id)
        return RuntimeReadResult(session.id, output=output, status=session.status, prompt_id=None)

    def write_input(self, session_id: str, value: str, *, prompt_id: str) -> InteractiveSessionRecord:
        process = self._processes.get(session_id)
        if process is None:
            return self.sessions.mark_recovery_required(session_id)
        session = self.sessions.record_stdin(session_id, prompt_id=prompt_id, answer=value.rstrip("\n"))
        self.runner.write_stdin(process, value)
        return session

    def status(self, session_id: str) -> RuntimeStatus:
        process = self._processes.get(session_id)
        if process is None:
            session = self.sessions.mark_recovery_required(session_id)
            return RuntimeStatus(session_id=session.id, status=session.status, process_id=session.process_id)

        exit_code = self.runner.poll(process)
        if exit_code is not None:
            session = self.sessions.mark_completed(session_id)
            self._processes.pop(session_id, None)
            return RuntimeStatus(session_id=session.id, status=session.status, process_id=session.process_id)

        session = self.sessions.get(session_id)
        return RuntimeStatus(session_id=session.id, status=session.status, process_id=session.process_id)

    def _detect_prompt_id(self, output: str) -> str | None:
        stripped = output.strip()
        if not stripped:
            return None
        if "?" not in stripped and not stripped.endswith(":"):
            return None
        digest = sha1(stripped.encode()).hexdigest()[:12]
        return f"prompt_{digest}"
```

- [ ] **Step 5: Verify runtime tests pass**

Run:

```bash
pytest tests/test_interactive_runtime.py -v
```

Expected:

```text
4 passed
```

## Task 3: Wire Runtime Into New Project Workflow

**Files:**
- Modify: `src/hermes_core/workflows/new_project.py`
- Modify: `tests/test_new_project_workflow.py`

- [ ] **Step 1: Add workflow runtime tests**

Append to `tests/test_new_project_workflow.py`:

```python
def test_workflow_can_start_live_interactive_process_and_submit_input(tmp_path):
    script = tmp_path / "ask.py"
    script.write_text(
        "answer = input('Project name? ')\nprint(f'created:{answer}')\n",
        encoding="utf-8",
    )
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = NewProjectWorkflowService(session_factory)

    started = service.start_larv_full(
        project_name="AeroTrack",
        command=["python3", str(script)],
        cwd=str(tmp_path),
        start_process=True,
    )
    read = service.read_interactive_output(started.interactive_session.id, timeout=2)
    assert read.status == "waiting_for_input"

    service.submit_human_input(
        started.interactive_session.id,
        prompt_id=read.prompt_id,
        answer="AeroTrack\n",
    )
    read = service.read_interactive_output(started.interactive_session.id, timeout=5)

    assert "created:AeroTrack" in read.output
    assert read.status == "completed"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_new_project_workflow.py::test_workflow_can_start_live_interactive_process_and_submit_input -v
```

Expected:

```text
TypeError: NewProjectWorkflowService.start_larv_full() got an unexpected keyword argument 'start_process'
```

- [ ] **Step 3: Add runtime to workflow service**

Modify `src/hermes_core/workflows/new_project.py`:

Add imports:

```python
from hermes_core.runtime.interactive import InteractiveRuntime, RuntimeReadResult
```

In `__init__`, add:

```python
        self.runtime = InteractiveRuntime(session_factory)
```

Change `start_larv_full` signature:

```python
        start_process: bool = False,
```

Replace the session creation block with:

```python
        if start_process:
            interactive_session = self.runtime.start(
                run_id=run.id,
                command=command,
                cwd=cwd,
                transcript_ref=transcript_ref,
            )
        else:
            interactive_session = self.sessions.create(
                run_id=run.id,
                command=command,
                cwd=cwd,
                transcript_ref=transcript_ref,
            )
```

Add method:

```python
    def read_interactive_output(self, session_id: str, *, timeout: float = 0.2) -> RuntimeReadResult:
        return self.runtime.read(session_id, timeout=timeout)
```

Update `submit_human_input` so it writes to runtime when the PTY is live:

```python
        if session_id in self.runtime._processes:
            interactive_session = self.runtime.write_input(session_id, answer, prompt_id=prompt_id)
        else:
            interactive_session = self.sessions.record_stdin(
                session_id,
                prompt_id=prompt_id,
                answer=answer,
            )
```

- [ ] **Step 4: Verify workflow runtime tests pass**

Run:

```bash
pytest tests/test_new_project_workflow.py -v
```

Expected:

```text
4 passed
```

## Task 4: Runtime API Endpoints

**Files:**
- Modify: `src/hermes_core/api/routes.py`
- Create: `tests/test_api_interactive_runtime.py`

- [ ] **Step 1: Write API runtime tests**

Create `tests/test_api_interactive_runtime.py`:

```python
from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_api_can_read_interactive_output_and_submit_stdin(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    script = tmp_path / "ask.py"
    script.write_text(
        "answer = input('Project name? ')\nprint(f'created:{answer}')\n",
        encoding="utf-8",
    )
    client = TestClient(create_app())
    started = client.post(
        "/workflows/new-project/larv-full/start",
        json={
            "project_name": "AeroTrack",
            "command": ["python3", str(script)],
            "cwd": str(tmp_path),
            "start_process": True,
        },
    ).json()
    session_id = started["interactive_session"]["id"]

    output = client.get(f"/interactive-sessions/{session_id}/output?timeout=2").json()
    assert "Project name?" in output["output"]
    assert output["status"] == "waiting_for_input"

    response = client.post(
        f"/interactive-sessions/{session_id}/stdin",
        json={
            "prompt_id": output["prompt_id"],
            "answer": "AeroTrack\n",
        },
    )
    assert response.status_code == 200

    output = client.get(f"/interactive-sessions/{session_id}/output?timeout=5").json()
    assert "created:AeroTrack" in output["output"]
    assert output["status"] == "completed"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_api_interactive_runtime.py -v
```

Expected:

```text
422 Unprocessable Entity or 404 until endpoint fields exist
```

- [ ] **Step 3: Update API request models and service lifetime**

Modify `src/hermes_core/api/routes.py`:

Add to `StartLarvFullRequest`:

```python
    start_process: bool = False
```

Add `start_process=request.start_process` to `service.start_larv_full(...)`.

Important: the API must reuse one in-process workflow service so live PTY handles survive across requests in tests and runtime.

Add module-level cache:

```python
_WORKFLOW_SERVICE: NewProjectWorkflowService | None = None
_WORKFLOW_DATABASE_URL: str | None = None
```

Replace `_workflow_service()` with:

```python
def _workflow_service() -> NewProjectWorkflowService:
    global _WORKFLOW_DATABASE_URL, _WORKFLOW_SERVICE
    settings = get_settings()
    if _WORKFLOW_SERVICE is not None and _WORKFLOW_DATABASE_URL == settings.database_url:
        return _WORKFLOW_SERVICE
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    _WORKFLOW_DATABASE_URL = settings.database_url
    _WORKFLOW_SERVICE = NewProjectWorkflowService(session_factory)
    return _WORKFLOW_SERVICE
```

Add endpoint:

```python
@router.get("/interactive-sessions/{session_id}/output")
def read_interactive_output(session_id: str, timeout: float = 0.2) -> dict[str, Any]:
    service = _workflow_service()
    result = service.read_interactive_output(session_id, timeout=timeout)
    return {
        "session_id": result.session_id,
        "output": result.output,
        "status": result.status,
        "prompt_id": result.prompt_id,
    }
```

- [ ] **Step 4: Verify API runtime tests pass**

Run:

```bash
pytest tests/test_api_interactive_runtime.py -v
```

Expected:

```text
1 passed
```

## Task 5: Runtime CLI Commands

**Files:**
- Modify: `src/hermes_core/cli.py`
- Create: `tests/test_cli_interactive_runtime.py`

- [ ] **Step 1: Write CLI runtime tests**

Create `tests/test_cli_interactive_runtime.py`:

```python
from typer.testing import CliRunner

from hermes_core.cli import app


def test_cli_runtime_read_reports_recovery_for_non_live_session(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    runner = CliRunner()
    started = runner.invoke(
        app,
        [
            "new-project-start",
            "AeroTrack",
            "--cwd",
            str(tmp_path),
            "--command",
            "larv:full",
        ],
    )
    session_id = [
        part.removeprefix("session_id=")
        for part in started.stdout.split()
        if part.startswith("session_id=")
    ][0]

    result = runner.invoke(app, ["session-output", session_id])

    assert result.exit_code == 0
    assert "status=recovery_required" in result.stdout
```

- [ ] **Step 2: Add CLI command**

Modify `src/hermes_core/cli.py`:

Add command:

```python
@app.command("session-output")
def session_output(session_id: str, timeout: float = 0.2) -> None:
    service = _new_project_service()
    result = service.read_interactive_output(session_id, timeout=timeout)
    typer.echo(f"session_id={result.session_id} status={result.status} prompt_id={result.prompt_id}")
    if result.output:
        typer.echo(result.output)
```

Do not try to keep a live PTY process across separate CLI invocations in this slice. Each CLI invocation is a separate process, so `session-output` correctly reports recovery-required for non-live process-local sessions.

- [ ] **Step 3: Verify CLI runtime tests pass**

Run:

```bash
pytest tests/test_cli_interactive_runtime.py -v
```

Expected:

```text
1 passed
```

## Task 6: Full Verification Without Commit

**Files:**
- Modify only if verification reveals concrete failures.

- [ ] **Step 1: Run full tests**

Run:

```bash
pytest tests -v
```

Expected:

```text
All tests pass.
```

- [ ] **Step 2: Run lint**

Run:

```bash
ruff check src tests profiles
```

Expected:

```text
All checks passed!
```

- [ ] **Step 3: Regenerate docs HTML**

Run:

```bash
node tools/build-hermes-docs.mjs
```

Expected:

```text
Rendered 10 Markdown files to /home/claude-team/mann/hermes-core/docs/hermes/index.html
```

- [ ] **Step 4: Report without committing**

Run:

```bash
git status --short
git diff --stat
```

Expected:

```text
Shows uncommitted runtime implementation changes.
No commit is made unless the user explicitly asks.
```

## Self-Review

Spec coverage:

```text
Live PTY registry: Task 2.
Start real interactive command: Task 2 and Task 3.
Read output and transcript persistence: Task 1 and Task 2.
Prompt detection: Task 2.
Submit input to live PTY: Task 2 and Task 3.
Completion detection: Task 2.
Recovery-required behavior: Task 2 and Task 5.
API access: Task 4.
CLI access: Task 5.
No fake larv:full completion: preserved. The runtime can execute a real command,
but actual larv:full smoke execution remains a later verification slice.
```

Placeholder scan:

```text
No placeholder markers are present.
```

Type consistency:

```text
InteractiveRuntime, RuntimeReadResult, RuntimeStatus, PtyProcess,
InteractiveSessionService, and NewProjectWorkflowService names are consistent.
```

