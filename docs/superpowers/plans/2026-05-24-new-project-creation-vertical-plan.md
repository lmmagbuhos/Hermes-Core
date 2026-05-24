# New Project Creation Vertical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real new-project workflow vertical: start a resumable `larv:full` interactive session, accept human answers by session ID, capture transcript history, ingest generated artifacts, create a temporary `ProjectContextCandidate`, and expose run/session inspection through CLI and API.

**Architecture:** Extend the current Hermes foundation with persisted interactive session records and a PTY-backed local runner. The `new_project_creation` workflow remains server-side and durable; DTT-AI integration is deferred, but the session and input APIs will match the future DTT-AI contract. `larv:full` is treated as an interactive discovery/scaffolding command, not as a fake simulated workflow.

**Tech Stack:** Python 3.12, FastAPI, Typer, SQLAlchemy 2, Pydantic v2, pytest, Ruff, standard-library `pty`, `select`, `os`, `signal`, and local filesystem artifact scanning.

---

## Scope

This plan implements the new-project vertical up to local/API/CLI control. It does not implement browser streaming, GitHub repo creation, or DTT-AI WebSocket/SSE integration.

Implemented by this plan:

```text
interactive session persistence
PTY-backed local interactive runner
stdin replay protection
transcript and prompt history storage
new_project_creation workflow service
larv:full command start/input/status flow
artifact ingestion into HermesProjectBlueprint
ProjectContextCandidate persistence
API and CLI access for sessions and blueprints
tests for all new behavior
```

Deferred:

```text
DTT-AI live terminal UI
WebSocket/SSE streaming
GitHub repo creation
permanent Hermes-{projectName} creation
parallel tactical workers
real worker execution after blueprint generation
```

## Target File Structure

```text
src/hermes_core/models.py
src/hermes_core/execution/contracts.py
src/hermes_core/execution/interactive.py
src/hermes_core/sessions/__init__.py
src/hermes_core/sessions/service.py
src/hermes_core/artifacts/__init__.py
src/hermes_core/artifacts/ingest.py
src/hermes_core/projects/__init__.py
src/hermes_core/projects/service.py
src/hermes_core/workflows/__init__.py
src/hermes_core/workflows/new_project.py
src/hermes_core/api/routes.py
src/hermes_core/cli.py
tests/test_interactive_sessions.py
tests/test_artifact_ingestion.py
tests/test_new_project_workflow.py
tests/test_api_new_project.py
tests/test_cli_new_project.py
```

## Task 1: Persist Interactive Sessions

**Files:**
- Modify: `src/hermes_core/models.py`
- Create: `src/hermes_core/sessions/__init__.py`
- Create: `src/hermes_core/sessions/service.py`
- Create: `tests/test_interactive_sessions.py`

- [ ] **Step 1: Write failing session persistence tests**

Create `tests/test_interactive_sessions.py`:

```python
from hermes_core.db import create_session_factory, init_db
from hermes_core.sessions.service import InteractiveSessionService


def test_creates_interactive_session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = InteractiveSessionService(session_factory)

    session = service.create(
        run_id=7,
        command=["larv:full"],
        cwd=str(tmp_path),
        transcript_ref="transcripts/sess_1.log",
    )

    assert session.id.startswith("sess_")
    assert session.run_id == 7
    assert session.status == "running"
    assert session.command == ["larv:full"]
    assert session.stdin_history == []
    assert session.prompt_history == []


def test_marks_waiting_for_input_and_records_prompt(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = InteractiveSessionService(session_factory)
    session = service.create(
        run_id=7,
        command=["larv:full"],
        cwd=str(tmp_path),
        transcript_ref="transcripts/sess_1.log",
    )

    updated = service.mark_waiting_for_input(
        session.id,
        prompt="Which backend stack should be used?",
        prompt_id="prompt_backend_stack",
    )

    assert updated.status == "waiting_for_input"
    assert updated.last_prompt == "Which backend stack should be used?"
    assert updated.prompt_history == [
        {
            "prompt_id": "prompt_backend_stack",
            "prompt": "Which backend stack should be used?",
        }
    ]


def test_records_stdin_once_per_prompt(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = InteractiveSessionService(session_factory)
    session = service.create(
        run_id=7,
        command=["larv:full"],
        cwd=str(tmp_path),
        transcript_ref="transcripts/sess_1.log",
    )
    service.mark_waiting_for_input(session.id, prompt="Choose stack", prompt_id="stack")

    first = service.record_stdin(session.id, prompt_id="stack", answer="Fastify")

    assert first.status == "resumed"
    assert first.stdin_history == [
        {
            "prompt_id": "stack",
            "answer": "Fastify",
        }
    ]

    try:
        service.record_stdin(session.id, prompt_id="stack", answer="Fastify")
    except ValueError as error:
        assert "already received stdin" in str(error)
    else:
        raise AssertionError("Expected duplicate stdin write to fail")
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_interactive_sessions.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'hermes_core.sessions'
```

- [ ] **Step 3: Add `InteractiveSessionRecord` model**

Modify `src/hermes_core/models.py` by adding:

```python
class InteractiveSessionRecord(Base):
    __tablename__ = "interactive_sessions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    command: Mapped[list[str]] = mapped_column(JSON, default=list)
    cwd: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    transcript_ref: Mapped[str] = mapped_column(String(1000), nullable=False)
    process_id: Mapped[int | None] = mapped_column(nullable=True)
    last_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_history: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    stdin_history: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )
```

- [ ] **Step 4: Create session service package**

Create `src/hermes_core/sessions/__init__.py`:

```python
"""Interactive session persistence and stdin replay protection."""
```

- [ ] **Step 5: Implement `InteractiveSessionService`**

Create `src/hermes_core/sessions/service.py`:

```python
from collections.abc import Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from hermes_core.models import InteractiveSessionRecord


class InteractiveSessionService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create(
        self,
        *,
        run_id: int,
        command: list[str],
        cwd: str,
        transcript_ref: str,
        process_id: int | None = None,
    ) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = InteractiveSessionRecord(
                id=f"sess_{uuid4().hex}",
                run_id=run_id,
                command=command,
                cwd=cwd,
                status="running",
                transcript_ref=transcript_ref,
                process_id=process_id,
                prompt_history=[],
                stdin_history=[],
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def get(self, session_id: str) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            return record

    def mark_waiting_for_input(
        self,
        session_id: str,
        *,
        prompt: str,
        prompt_id: str,
    ) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            record.status = "waiting_for_input"
            record.last_prompt = prompt
            record.prompt_history = [
                *(record.prompt_history or []),
                {
                    "prompt_id": prompt_id,
                    "prompt": prompt,
                },
            ]
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def record_stdin(
        self,
        session_id: str,
        *,
        prompt_id: str,
        answer: str,
    ) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            history = record.stdin_history or []
            if any(item["prompt_id"] == prompt_id for item in history):
                raise ValueError(f"Prompt {prompt_id} already received stdin")
            record.status = "resumed"
            record.stdin_history = [
                *history,
                {
                    "prompt_id": prompt_id,
                    "answer": answer,
                },
            ]
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
```

- [ ] **Step 6: Verify session persistence tests pass**

Run:

```bash
pytest tests/test_interactive_sessions.py -v
```

Expected:

```text
3 passed
```

## Task 2: PTY-Backed Interactive Runner

**Files:**
- Modify: `src/hermes_core/execution/contracts.py`
- Create: `src/hermes_core/execution/interactive.py`
- Modify: `tests/test_interactive_sessions.py`

- [ ] **Step 1: Add interactive runner tests**

Append to `tests/test_interactive_sessions.py`:

```python
from hermes_core.execution.interactive import PtyInteractiveRunner


def test_pty_runner_starts_reads_writes_and_completes(tmp_path):
    script = tmp_path / "ask.py"
    script.write_text(
        "answer = input('Project name? ')\nprint(f'created:{answer}')\n",
        encoding="utf-8",
    )
    runner = PtyInteractiveRunner()

    process = runner.start(["python3", str(script)], cwd=str(tmp_path))
    output = runner.read_available(process, timeout=2)
    assert "Project name?" in output

    runner.write_stdin(process, "AeroTrack\n")
    output = runner.read_until_complete(process, timeout=5)

    assert "created:AeroTrack" in output
    assert runner.poll(process) == 0
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_interactive_sessions.py::test_pty_runner_starts_reads_writes_and_completes -v
```

Expected:

```text
ModuleNotFoundError: No module named 'hermes_core.execution.interactive'
```

- [ ] **Step 3: Add PTY process contract**

Modify `src/hermes_core/execution/contracts.py` by adding:

```python
class PtyProcess(BaseModel):
    pid: int
    fd: int
    command: list[str]
    cwd: str
```

- [ ] **Step 4: Implement PTY runner**

Create `src/hermes_core/execution/interactive.py`:

```python
import errno
import os
import pty
import select
import signal
import time

from hermes_core.execution.contracts import PtyProcess


class PtyInteractiveRunner:
    def start(self, command: list[str], cwd: str) -> PtyProcess:
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(cwd)
            os.execvp(command[0], command)
        os.set_blocking(fd, False)
        return PtyProcess(pid=pid, fd=fd, command=command, cwd=cwd)

    def read_available(self, process: PtyProcess, timeout: float = 0.2) -> str:
        chunks: list[str] = []
        end_at = time.monotonic() + timeout
        while time.monotonic() < end_at:
            readable, _, _ = select.select([process.fd], [], [], 0.05)
            if not readable:
                continue
            try:
                data = os.read(process.fd, 4096)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            if not data:
                break
            chunks.append(data.decode(errors="replace"))
        return "".join(chunks)

    def write_stdin(self, process: PtyProcess, value: str) -> None:
        os.write(process.fd, value.encode())

    def poll(self, process: PtyProcess) -> int | None:
        pid, status = os.waitpid(process.pid, os.WNOHANG)
        if pid == 0:
            return None
        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)
        if os.WIFSIGNALED(status):
            return 128 + os.WTERMSIG(status)
        return status

    def read_until_complete(self, process: PtyProcess, timeout: float = 30) -> str:
        output: list[str] = []
        end_at = time.monotonic() + timeout
        while time.monotonic() < end_at:
            output.append(self.read_available(process, timeout=0.2))
            if self.poll(process) is not None:
                output.append(self.read_available(process, timeout=0.2))
                return "".join(output)
        raise TimeoutError(f"Process did not complete before {timeout} seconds")

    def terminate(self, process: PtyProcess) -> None:
        os.kill(process.pid, signal.SIGTERM)
```

- [ ] **Step 5: Verify PTY test passes**

Run:

```bash
pytest tests/test_interactive_sessions.py::test_pty_runner_starts_reads_writes_and_completes -v
```

Expected:

```text
1 passed
```

## Task 3: Artifact Ingestion

**Files:**
- Create: `src/hermes_core/artifacts/__init__.py`
- Create: `src/hermes_core/artifacts/ingest.py`
- Create: `tests/test_artifact_ingestion.py`

- [ ] **Step 1: Write artifact ingestion tests**

Create `tests/test_artifact_ingestion.py`:

```python
from hermes_core.artifacts.ingest import ingest_project_artifacts


def test_ingests_generated_project_artifacts(tmp_path):
    project = tmp_path / "AeroTrack"
    project.mkdir()
    (project / "package.json").write_text('{"packageManager":"pnpm@9.0.0"}', encoding="utf-8")
    docs = project / "docs" / "Handsoff"
    docs.mkdir(parents=True)
    (docs / "slice-01-backend.md").write_text("# Backend Slice\nBuild API", encoding="utf-8")

    blueprint = ingest_project_artifacts(
        project_dir=project,
        transcript="Human chose Fastify and Next.js.",
    )

    assert blueprint.project_name == "AeroTrack"
    assert blueprint.package_manager == "pnpm"
    assert blueprint.transcript_summary == "Human chose Fastify and Next.js."
    assert blueprint.implementation_slices == ["docs/Handsoff/slice-01-backend.md"]
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_artifact_ingestion.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'hermes_core.artifacts'
```

- [ ] **Step 3: Implement artifact ingestion package**

Create `src/hermes_core/artifacts/__init__.py`:

```python
"""Project artifact ingestion."""
```

- [ ] **Step 4: Implement `HermesProjectBlueprint` and ingestion**

Create `src/hermes_core/artifacts/ingest.py`:

```python
import json
from pathlib import Path

from pydantic import BaseModel


class HermesProjectBlueprint(BaseModel):
    project_name: str
    project_dir: str
    package_manager: str | None
    implementation_slices: list[str]
    transcript_summary: str


def ingest_project_artifacts(project_dir: Path, transcript: str) -> HermesProjectBlueprint:
    package_manager = _detect_package_manager(project_dir)
    slices = sorted(
        str(path.relative_to(project_dir))
        for path in project_dir.glob("docs/Handsoff/slice-*.md")
    )
    return HermesProjectBlueprint(
        project_name=project_dir.name,
        project_dir=str(project_dir),
        package_manager=package_manager,
        implementation_slices=slices,
        transcript_summary=transcript.strip(),
    )


def _detect_package_manager(project_dir: Path) -> str | None:
    package_json = project_dir / "package.json"
    if not package_json.exists():
        return None
    data = json.loads(package_json.read_text(encoding="utf-8"))
    package_manager = data.get("packageManager")
    if isinstance(package_manager, str) and package_manager:
        return package_manager.split("@", maxsplit=1)[0]
    if (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_dir / "yarn.lock").exists():
        return "yarn"
    if (project_dir / "package-lock.json").exists():
        return "npm"
    return None
```

- [ ] **Step 5: Verify artifact tests pass**

Run:

```bash
pytest tests/test_artifact_ingestion.py -v
```

Expected:

```text
1 passed
```

## Task 4: ProjectContextCandidate Persistence

**Files:**
- Modify: `src/hermes_core/models.py`
- Create: `src/hermes_core/projects/__init__.py`
- Create: `src/hermes_core/projects/service.py`
- Modify: `tests/test_artifact_ingestion.py`

- [ ] **Step 1: Add candidate persistence test**

Append to `tests/test_artifact_ingestion.py`:

```python
from hermes_core.db import create_session_factory, init_db
from hermes_core.projects.service import ProjectContextCandidateService


def test_creates_project_context_candidate(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = ProjectContextCandidateService(session_factory)

    candidate = service.create(
        run_id=9,
        project_name="AeroTrack",
        blueprint={
            "project_name": "AeroTrack",
            "package_manager": "pnpm",
            "implementation_slices": ["docs/Handsoff/slice-01-backend.md"],
        },
    )

    assert candidate.id is not None
    assert candidate.status == "candidate"
    assert candidate.blueprint["package_manager"] == "pnpm"
```

- [ ] **Step 2: Add model**

Modify `src/hermes_core/models.py` by adding:

```python
class ProjectContextCandidate(Base):
    __tablename__ = "project_context_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    blueprint: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )
```

- [ ] **Step 3: Create projects package**

Create `src/hermes_core/projects/__init__.py`:

```python
"""Project context candidate services."""
```

- [ ] **Step 4: Implement candidate service**

Create `src/hermes_core/projects/service.py`:

```python
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from hermes_core.models import ProjectContextCandidate


class ProjectContextCandidateService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create(
        self,
        *,
        run_id: int,
        project_name: str,
        blueprint: dict[str, Any],
    ) -> ProjectContextCandidate:
        with self.session_factory() as db:
            candidate = ProjectContextCandidate(
                run_id=run_id,
                project_name=project_name,
                blueprint=blueprint,
                status="candidate",
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            return candidate
```

- [ ] **Step 5: Verify candidate tests pass**

Run:

```bash
pytest tests/test_artifact_ingestion.py -v
```

Expected:

```text
2 passed
```

## Task 5: New Project Workflow Service

**Files:**
- Create: `src/hermes_core/workflows/__init__.py`
- Create: `src/hermes_core/workflows/new_project.py`
- Create: `tests/test_new_project_workflow.py`

- [ ] **Step 1: Write workflow service tests**

Create `tests/test_new_project_workflow.py`:

```python
from hermes_core.db import create_session_factory, init_db
from hermes_core.models import Event
from hermes_core.workflows.new_project import NewProjectWorkflowService


def test_starts_new_project_larv_session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = NewProjectWorkflowService(session_factory)

    result = service.start_larv_full(
        project_name="AeroTrack",
        command=["python3", "-c", "print('larv placeholder')"],
        cwd=str(tmp_path),
    )

    assert result.run.workflow_type == "new_project_creation"
    assert result.run.state == "larv_full_session_started"
    assert result.interactive_session.status == "running"
    assert result.interactive_session.command == ["python3", "-c", "print('larv placeholder')"]


def test_records_human_input_for_larv_session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = NewProjectWorkflowService(session_factory)
    result = service.start_larv_full(
        project_name="AeroTrack",
        command=["larv:full"],
        cwd=str(tmp_path),
    )
    service.waiting_for_input(
        result.interactive_session.id,
        prompt_id="stack",
        prompt="Choose stack",
    )

    updated = service.submit_human_input(
        result.interactive_session.id,
        prompt_id="stack",
        answer="Fastify and Next.js",
    )

    assert updated.interactive_session.status == "resumed"
    assert updated.run.state == "larv_full_input_received"

    with session_factory() as db:
        events = db.query(Event).order_by(Event.id).all()
    assert "human.input_received" in [event.type for event in events]
```

- [ ] **Step 2: Create workflows package**

Create `src/hermes_core/workflows/__init__.py`:

```python
"""Workflow orchestration services."""
```

- [ ] **Step 3: Implement new-project workflow service**

Create `src/hermes_core/workflows/new_project.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from hermes_core.events.service import EventService
from hermes_core.models import InteractiveSessionRecord, Run
from hermes_core.runs.service import RunService
from hermes_core.sessions.service import InteractiveSessionService


@dataclass(frozen=True)
class NewProjectWorkflowResult:
    run: Run
    interactive_session: InteractiveSessionRecord


class NewProjectWorkflowService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory
        self.runs = RunService(session_factory)
        self.sessions = InteractiveSessionService(session_factory)
        self.events = EventService(session_factory)

    def start_larv_full(
        self,
        *,
        project_name: str,
        command: list[str],
        cwd: str,
    ) -> NewProjectWorkflowResult:
        run = self.runs.create_run(
            "new_project_creation",
            {
                "project_name": project_name,
                "cwd": cwd,
            },
        )
        transcript_ref = str(Path(cwd) / ".hermes" / "transcripts" / f"run_{run.id}.log")
        interactive_session = self.sessions.create(
            run_id=run.id,
            command=command,
            cwd=cwd,
            transcript_ref=transcript_ref,
        )
        run = self.runs.transition(
            run.id,
            "larv_full_session_started",
            {"interactive_session_id": interactive_session.id},
        )
        self.events.emit(
            "terminal.session_started",
            {"session_id": interactive_session.id, "command": command},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def waiting_for_input(
        self,
        session_id: str,
        *,
        prompt_id: str,
        prompt: str,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.mark_waiting_for_input(
            session_id,
            prompt=prompt,
            prompt_id=prompt_id,
        )
        run = self.runs.transition(
            interactive_session.run_id,
            "larv_full_waiting_for_input",
            {"last_prompt": prompt, "last_prompt_id": prompt_id},
        )
        self.events.emit(
            "human.input_required",
            {"session_id": session_id, "prompt_id": prompt_id, "prompt": prompt},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def submit_human_input(
        self,
        session_id: str,
        *,
        prompt_id: str,
        answer: str,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.record_stdin(
            session_id,
            prompt_id=prompt_id,
            answer=answer,
        )
        run = self.runs.transition(
            interactive_session.run_id,
            "larv_full_input_received",
            {"last_answer_prompt_id": prompt_id},
        )
        self.events.emit(
            "human.input_received",
            {"session_id": session_id, "prompt_id": prompt_id},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)
```

- [ ] **Step 4: Verify workflow tests pass**

Run:

```bash
pytest tests/test_new_project_workflow.py -v
```

Expected:

```text
2 passed
```

## Task 6: Complete and Ingest New Project Artifacts

**Files:**
- Modify: `src/hermes_core/workflows/new_project.py`
- Modify: `tests/test_new_project_workflow.py`

- [ ] **Step 1: Add completion/ingestion test**

Append to `tests/test_new_project_workflow.py`:

```python
from hermes_core.models import ProjectContextCandidate


def test_completes_larv_full_and_creates_project_context_candidate(tmp_path):
    project = tmp_path / "AeroTrack"
    project.mkdir()
    (project / "package.json").write_text('{"packageManager":"pnpm@9.0.0"}', encoding="utf-8")
    handsoff = project / "docs" / "Handsoff"
    handsoff.mkdir(parents=True)
    (handsoff / "slice-01-backend.md").write_text("# Backend", encoding="utf-8")

    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = NewProjectWorkflowService(session_factory)
    started = service.start_larv_full(
        project_name="AeroTrack",
        command=["larv:full"],
        cwd=str(project),
    )

    completed = service.complete_larv_full(
        started.interactive_session.id,
        transcript="Human chose Fastify and Next.js.",
        project_dir=project,
    )

    assert completed.run.state == "project_context_candidate_created"
    with session_factory() as db:
        candidate = db.query(ProjectContextCandidate).one()
    assert candidate.project_name == "AeroTrack"
    assert candidate.blueprint["package_manager"] == "pnpm"
```

- [ ] **Step 2: Implement completion method**

Modify `src/hermes_core/workflows/new_project.py` to import:

```python
from hermes_core.artifacts.ingest import ingest_project_artifacts
from hermes_core.projects.service import ProjectContextCandidateService
```

Add `self.candidates = ProjectContextCandidateService(session_factory)` in `__init__`.

Add this method:

```python
    def complete_larv_full(
        self,
        session_id: str,
        *,
        transcript: str,
        project_dir: Path,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.get(session_id)
        run = self.runs.transition(interactive_session.run_id, "larv_full_completed")
        blueprint = ingest_project_artifacts(project_dir=project_dir, transcript=transcript)
        run = self.runs.transition(
            run.id,
            "larv_artifacts_ingested",
            {"blueprint": blueprint.model_dump()},
        )
        candidate = self.candidates.create(
            run_id=run.id,
            project_name=blueprint.project_name,
            blueprint=blueprint.model_dump(),
        )
        run = self.runs.transition(
            run.id,
            "project_context_candidate_created",
            {"project_context_candidate_id": candidate.id},
        )
        self.events.emit(
            "artifact.blueprint_created",
            {"project_name": blueprint.project_name, "candidate_id": candidate.id},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)
```

- [ ] **Step 3: Verify completion tests pass**

Run:

```bash
pytest tests/test_new_project_workflow.py -v
```

Expected:

```text
3 passed
```

## Task 7: API Endpoints for New Project Workflow

**Files:**
- Modify: `src/hermes_core/api/routes.py`
- Create: `tests/test_api_new_project.py`

- [ ] **Step 1: Write API tests**

Create `tests/test_api_new_project.py`:

```python
from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_api_starts_new_project_larv_session(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/workflows/new-project/larv-full/start",
        json={
            "project_name": "AeroTrack",
            "command": ["larv:full"],
            "cwd": str(tmp_path),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run"]["state"] == "larv_full_session_started"
    assert body["interactive_session"]["status"] == "running"


def test_api_submits_human_input(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    client = TestClient(create_app())
    started = client.post(
        "/workflows/new-project/larv-full/start",
        json={
            "project_name": "AeroTrack",
            "command": ["larv:full"],
            "cwd": str(tmp_path),
        },
    ).json()
    session_id = started["interactive_session"]["id"]
    client.post(
        f"/interactive-sessions/{session_id}/waiting-for-input",
        json={
            "prompt_id": "stack",
            "prompt": "Choose stack",
        },
    )

    response = client.post(
        f"/interactive-sessions/{session_id}/stdin",
        json={
            "prompt_id": "stack",
            "answer": "Fastify",
        },
    )

    assert response.status_code == 200
    assert response.json()["run"]["state"] == "larv_full_input_received"
```

- [ ] **Step 2: Add request models and helpers to routes**

Modify `src/hermes_core/api/routes.py` by adding imports:

```python
from pathlib import Path
from hermes_core.workflows.new_project import NewProjectWorkflowResult, NewProjectWorkflowService
```

Add request models:

```python
class StartLarvFullRequest(BaseModel):
    project_name: str
    command: list[str]
    cwd: str


class WaitingForInputRequest(BaseModel):
    prompt_id: str
    prompt: str


class SubmitInputRequest(BaseModel):
    prompt_id: str
    answer: str
```

Add helper:

```python
def _workflow_service() -> NewProjectWorkflowService:
    settings = get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    return NewProjectWorkflowService(session_factory)


def _workflow_result_payload(result: NewProjectWorkflowResult) -> dict[str, Any]:
    return {
        "run": {
            "id": result.run.id,
            "workflow_type": result.run.workflow_type,
            "state": result.run.state,
            "payload": result.run.payload,
        },
        "interactive_session": {
            "id": result.interactive_session.id,
            "run_id": result.interactive_session.run_id,
            "command": result.interactive_session.command,
            "cwd": result.interactive_session.cwd,
            "status": result.interactive_session.status,
            "last_prompt": result.interactive_session.last_prompt,
            "transcript_ref": result.interactive_session.transcript_ref,
        },
    }
```

Add endpoints:

```python
@router.post("/workflows/new-project/larv-full/start")
def start_larv_full(request: StartLarvFullRequest) -> dict[str, Any]:
    service = _workflow_service()
    result = service.start_larv_full(
        project_name=request.project_name,
        command=request.command,
        cwd=request.cwd,
    )
    return _workflow_result_payload(result)


@router.post("/interactive-sessions/{session_id}/waiting-for-input")
def mark_waiting_for_input(
    session_id: str,
    request: WaitingForInputRequest,
) -> dict[str, Any]:
    service = _workflow_service()
    result = service.waiting_for_input(
        session_id,
        prompt_id=request.prompt_id,
        prompt=request.prompt,
    )
    return _workflow_result_payload(result)


@router.post("/interactive-sessions/{session_id}/stdin")
def submit_stdin(session_id: str, request: SubmitInputRequest) -> dict[str, Any]:
    service = _workflow_service()
    result = service.submit_human_input(
        session_id,
        prompt_id=request.prompt_id,
        answer=request.answer,
    )
    return _workflow_result_payload(result)
```

- [ ] **Step 3: Verify API tests pass**

Run:

```bash
pytest tests/test_api_new_project.py -v
```

Expected:

```text
2 passed
```

## Task 8: CLI Commands for New Project Workflow

**Files:**
- Modify: `src/hermes_core/cli.py`
- Create: `tests/test_cli_new_project.py`

- [ ] **Step 1: Write CLI tests**

Create `tests/test_cli_new_project.py`:

```python
from typer.testing import CliRunner

from hermes_core.cli import app


def test_cli_starts_new_project_run(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    runner = CliRunner()

    result = runner.invoke(
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

    assert result.exit_code == 0
    assert "run_id=" in result.stdout
    assert "session_id=sess_" in result.stdout


def test_cli_submits_session_input(tmp_path, monkeypatch):
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
    runner.invoke(app, ["session-waiting", session_id, "stack", "Choose stack"])

    result = runner.invoke(app, ["session-input", session_id, "stack", "Fastify"])

    assert result.exit_code == 0
    assert "state=larv_full_input_received" in result.stdout
```

- [ ] **Step 2: Add CLI helpers and commands**

Modify `src/hermes_core/cli.py` by adding imports:

```python
from hermes_core.workflows.new_project import NewProjectWorkflowService
```

Add helper:

```python
def _new_project_service() -> NewProjectWorkflowService:
    settings = get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    return NewProjectWorkflowService(session_factory)
```

Add commands:

```python
@app.command("new-project-start")
def new_project_start(
    project_name: str,
    cwd: str = typer.Option(...),
    command: list[str] = typer.Option(...),
) -> None:
    service = _new_project_service()
    result = service.start_larv_full(project_name=project_name, command=command, cwd=cwd)
    typer.echo(f"run_id={result.run.id} session_id={result.interactive_session.id}")


@app.command("session-waiting")
def session_waiting(session_id: str, prompt_id: str, prompt: str) -> None:
    service = _new_project_service()
    result = service.waiting_for_input(session_id, prompt_id=prompt_id, prompt=prompt)
    typer.echo(f"run_id={result.run.id} state={result.run.state}")


@app.command("session-input")
def session_input(session_id: str, prompt_id: str, answer: str) -> None:
    service = _new_project_service()
    result = service.submit_human_input(session_id, prompt_id=prompt_id, answer=answer)
    typer.echo(f"run_id={result.run.id} state={result.run.state}")
```

- [ ] **Step 3: Verify CLI tests pass**

Run:

```bash
pytest tests/test_cli_new_project.py -v
```

Expected:

```text
2 passed
```

## Task 9: Full Verification and Commit

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

- [ ] **Step 4: Commit**

Run:

```bash
git add src tests docs/superpowers/plans/2026-05-24-new-project-creation-vertical-plan.md
git commit -m "feat: add new project creation workflow foundation"
```

Expected:

```text
[main <sha>] feat: add new project creation workflow foundation
```

## Self-Review

Spec coverage:

```text
Resumable session IDs: Tasks 1, 5, 7, 8.
larv:full waiting/input/resume states: Tasks 1 and 5.
Transcript reference and prompt/stdin history: Task 1.
PTY-backed interactive runner: Task 2.
Artifact ingestion into blueprint: Task 3.
ProjectContextCandidate: Task 4.
New-project workflow transitions: Tasks 5 and 6.
API/CLI control surfaces: Tasks 7 and 8.
No fake completion of project build: preserved. This plan starts and manages the
new-project vertical but does not claim workers completed implementation.
```

Placeholder scan:

```text
No placeholder markers are present.
Every task contains explicit files, test code, implementation code, commands,
and expected outputs.
```

Type consistency:

```text
InteractiveSessionRecord, ProjectContextCandidate, NewProjectWorkflowService,
NewProjectWorkflowResult, HermesProjectBlueprint, and route payload names are
consistent across tasks.
```
