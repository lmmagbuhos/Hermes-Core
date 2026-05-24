# Hermes Core Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real `hermes-core` foundation: structured agent profiles, workflow run state, policy checks, memory records, execution adapter boundaries, and a CLI/API surface that can later drive real `larv:full` and issue-fix workflows.

**Architecture:** Implement a Python/FastAPI service with a small explicit run-state model and a CLI for local operation. Use structured profile manifests as source-controlled bot identities, SQLite for local development storage, SQLAlchemy for persistence, and Pydantic models for contracts. This foundation does not fake project creation or issue fixing; it creates the durable kernel those real vertical workflows will use.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Typer, pytest, Ruff, MiniMax API adapter stub with real request boundary, SQLite locally with Postgres-ready schema.

---

## Scope Split

The full Hermes system is too large for one implementation pass. Implement it in these plans:

```text
Plan 1: Hermes Core Foundation
  Profiles, run-state engine, policy layer, memory records, event log, CLI/API skeleton.

Plan 2: New Project Creation Vertical
  Real larv:full interactive session, artifact ingestion, ProjectContextCandidate,
  sequential worker planning, validation report.

Plan 3: Issue Fix Vertical
  Ticket normalization, project-agent lookup, MAD scoring, solo/assembly mode,
  real patch execution, QA verification, report before PR/push.

Plan 4: DTT-AI Integration
  Event stream, terminal session bridge, human input API, approvals, reconnect.

Plan 5: GitHub Integration
  Branching, PR creation, repo creation, credentials, audit events.
```

This file covers Plan 1 only.

## Target File Structure

```text
pyproject.toml
README.md
.env.example
src/hermes_core/__init__.py
src/hermes_core/config.py
src/hermes_core/app.py
src/hermes_core/cli.py
src/hermes_core/db.py
src/hermes_core/models.py
src/hermes_core/profiles/loader.py
src/hermes_core/profiles/compiler.py
src/hermes_core/policy/rules.py
src/hermes_core/policy/service.py
src/hermes_core/runs/state.py
src/hermes_core/runs/service.py
src/hermes_core/events/service.py
src/hermes_core/memory/service.py
src/hermes_core/execution/contracts.py
src/hermes_core/execution/local.py
src/hermes_core/llm/minimax.py
src/hermes_core/api/routes.py
profiles/hermes-triage.yaml
profiles/hermes-manager.yaml
profiles/hermes-project-manager.yaml
profiles/hermes-frontend.yaml
profiles/hermes-backend.yaml
profiles/hermes-database.yaml
profiles/hermes-qa.yaml
tests/test_profiles.py
tests/test_policy.py
tests/test_runs.py
tests/test_memory.py
tests/test_api.py
```

## Task 1: Project Skeleton and Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/hermes_core/__init__.py`

- [ ] **Step 1: Create Python package configuration**

Create `pyproject.toml` with:

```toml
[project]
name = "hermes-core"
version = "0.1.0"
description = "Workflow-first AI orchestration core for Project Hermes"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.13.0",
  "fastapi>=0.111.0",
  "httpx>=0.27.0",
  "pydantic>=2.7.0",
  "pydantic-settings>=2.2.0",
  "python-dotenv>=1.0.0",
  "pyyaml>=6.0.1",
  "sqlalchemy>=2.0.30",
  "typer>=0.12.3",
  "uvicorn>=0.30.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "pytest-asyncio>=0.23.0",
  "ruff>=0.4.0",
]

[project.scripts]
hermes-core = "hermes_core.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/hermes_core"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create environment example**

Create `.env.example`:

```env
HERMES_DATABASE_URL=sqlite:///./hermes.db
HERMES_PROFILE_DIR=profiles
HERMES_MINIMAX_API_KEY=
HERMES_MINIMAX_BASE_URL=https://api.minimax.chat/v1
HERMES_MINIMAX_MODEL=
```

- [ ] **Step 3: Create README**

Create `README.md`:

```markdown
# Hermes Core

Hermes Core is the workflow-first AI orchestration layer for Project Hermes.

The Markdown architecture docs live in `docs/hermes/`.

## Local Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

## Documentation

Generate the browsable docs:

```bash
node tools/build-hermes-docs.mjs
```

Open `docs/hermes/index.html`.
```

- [ ] **Step 4: Add package marker**

Create `src/hermes_core/__init__.py`:

```python
"""Hermes Core package."""
```

- [ ] **Step 5: Verify project metadata**

Run:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

Expected:

```text
No tests collected, no import/install errors.
```

## Task 2: Configuration and Database Foundation

**Files:**
- Create: `src/hermes_core/config.py`
- Create: `src/hermes_core/db.py`
- Create: `src/hermes_core/models.py`
- Create: `tests/test_runs.py`

- [ ] **Step 1: Write database initialization test**

Create `tests/test_runs.py` with:

```python
from hermes_core.db import create_session_factory, init_db
from hermes_core.models import Run


def test_database_initializes_and_persists_run(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)

    with session_factory() as session:
        run = Run(workflow_type="issue_fix", state="received")
        session.add(run)
        session.commit()
        session.refresh(run)
        assert run.id is not None

    with session_factory() as session:
        saved = session.get(Run, 1)
        assert saved.workflow_type == "issue_fix"
        assert saved.state == "received"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_runs.py -v
```

Expected failure:

```text
ModuleNotFoundError or missing hermes_core.db
```

- [ ] **Step 3: Implement settings**

Create `src/hermes_core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./hermes.db"
    profile_dir: str = "profiles"
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.chat/v1"
    minimax_model: str = ""

    model_config = SettingsConfigDict(env_prefix="HERMES_", env_file=".env", extra="ignore")


def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Implement SQLAlchemy models**

Create `src/hermes_core/models.py`:

```python
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int | None] = mapped_column(nullable=True)
    type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    scope: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="candidate")
    confidence: Mapped[float] = mapped_column(default=0.0)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_run_id: Mapped[int | None] = mapped_column(nullable=True)
    created_by_agent: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 5: Implement database helpers**

Create `src/hermes_core/db.py`:

```python
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from hermes_core.config import get_settings
from hermes_core.models import Base


def create_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    engine = create_engine(database_url, future=True)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    settings = get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    with session_factory() as session:
        yield session
```

- [ ] **Step 6: Verify test passes**

Run:

```bash
pytest tests/test_runs.py -v
```

Expected:

```text
1 passed
```

## Task 3: Agent Profile Manifests and Loader

**Files:**
- Create: `profiles/hermes-triage.yaml`
- Create: `profiles/hermes-manager.yaml`
- Create: `profiles/hermes-project-manager.yaml`
- Create: `profiles/hermes-frontend.yaml`
- Create: `profiles/hermes-backend.yaml`
- Create: `profiles/hermes-database.yaml`
- Create: `profiles/hermes-qa.yaml`
- Create: `src/hermes_core/profiles/loader.py`
- Create: `tests/test_profiles.py`

- [ ] **Step 1: Write profile loader tests**

Create `tests/test_profiles.py`:

```python
from hermes_core.profiles.loader import load_profile, load_profiles


def test_loads_triage_profile():
    profile = load_profile("profiles/hermes-triage.yaml")
    assert profile.id == "hermes-triage"
    assert profile.name == "Hermes-Triage"
    assert "ticket.normalize" in profile.allowed_tools
    assert "repo.apply_patch" in profile.denied_tools


def test_loads_all_required_profiles():
    profiles = load_profiles("profiles")
    ids = {profile.id for profile in profiles}
    assert {
        "hermes-triage",
        "hermes-manager",
        "hermes-project-manager",
        "hermes-frontend",
        "hermes-backend",
        "hermes-database",
        "hermes-qa",
    }.issubset(ids)
```

- [ ] **Step 2: Create Hermes-Triage manifest**

Create `profiles/hermes-triage.yaml`:

```yaml
id: hermes-triage
name: Hermes-Triage
type: triage
version: 1
role_contract: Normalize requests, extract acceptance criteria, and reject ambiguity.
responsibilities:
  - Normalize messy tickets and project requests.
  - Extract target project, repository, issue summary, and acceptance criteria.
  - Reject unsafe or ambiguous work before execution.
non_responsibilities:
  - Modify source code.
  - Run terminal commands.
  - Approve policy exceptions.
allowed_tools:
  - ticket.normalize
  - workflow.emit_event
denied_tools:
  - repo.apply_patch
  - terminal.run_command
  - memory.promote
memory_sources:
  - global_policy
learning_rules:
  auto_candidate_types:
    - ambiguity_pattern
confidence_rubric:
  ambiguity_rejection_threshold: 0.7
escalation_rules:
  - Ask for clarification when acceptance criteria are missing.
review_rules: []
communication_style: concise
model_config:
  provider: minimax
```

- [ ] **Step 3: Create remaining manifests**

Create the remaining YAML files with the same keys. Minimum required role/tool distinctions:

```yaml
# profiles/hermes-manager.yaml
id: hermes-manager
name: Hermes-Manager
type: manager
version: 1
role_contract: Enforce security, policy, workflow gates, and final governance.
responsibilities:
  - Enforce security and workflow policy.
  - Audit high-risk actions.
  - Review learning promotion for project patterns and governance changes.
non_responsibilities:
  - Perform routine code edits directly.
allowed_tools:
  - policy.evaluate
  - memory.review
  - workflow.emit_event
denied_tools:
  - repo.apply_patch
  - terminal.write_stdin
memory_sources:
  - global_policy
learning_rules:
  auto_candidate_types: []
confidence_rubric: {}
escalation_rules:
  - Require governance gate for permission expansion.
review_rules:
  - human_checkpoint_required_before_issue_pr
communication_style: concise
model_config:
  provider: minimax
```

```yaml
# profiles/hermes-project-manager.yaml
id: hermes-project-manager
name: Hermes-ProjectManager
type: project_manager
version: 1
role_contract: Orchestrate workflows, create worker plans, and coordinate delivery.
responsibilities:
  - Create sequential worker plans.
  - Participate in MAD confidence scoring.
  - Coordinate tactical agents.
non_responsibilities:
  - Bypass Manager policy decisions.
allowed_tools:
  - workflow.transition
  - workflow.emit_event
  - policy.evaluate
  - terminal.start_interactive
denied_tools:
  - memory.promote_governance
memory_sources:
  - project_memory
  - run_notes
learning_rules:
  auto_candidate_types:
    - workflow_pattern
confidence_rubric:
  solo_threshold: 90
escalation_rules:
  - Use Assembly Line Mode when C_Final is below 90.
review_rules: []
communication_style: direct
model_config:
  provider: minimax
```

```yaml
# profiles/hermes-frontend.yaml
id: hermes-frontend
name: Hermes-Frontend
type: tactical_worker
version: 1
role_contract: Implement frontend changes within assigned scope.
responsibilities:
  - Frontend components, routes, client state, and frontend API integration.
non_responsibilities:
  - Database migrations.
  - Backend auth policy changes.
allowed_tools:
  - repo.read_file
  - repo.search
  - repo.apply_patch
  - terminal.run_command
denied_tools:
  - memory.promote
memory_sources:
  - project_memory
  - run_notes
learning_rules:
  auto_candidate_types:
    - frontend_fact
confidence_rubric: {}
escalation_rules:
  - Escalate when frontend change requires backend contract changes.
review_rules: []
communication_style: concise
model_config:
  provider: minimax
```

```yaml
# profiles/hermes-backend.yaml
id: hermes-backend
name: Hermes-Backend
type: tactical_worker
version: 1
role_contract: Implement backend changes within assigned scope.
responsibilities:
  - API endpoints, services, validation, backend tests, and backend conventions.
non_responsibilities:
  - UI behavior.
  - Unapproved schema changes.
allowed_tools:
  - repo.read_file
  - repo.search
  - repo.apply_patch
  - terminal.run_command
denied_tools:
  - memory.promote
memory_sources:
  - project_memory
  - run_notes
learning_rules:
  auto_candidate_types:
    - backend_fact
confidence_rubric: {}
escalation_rules:
  - Escalate auth, payment, and security-adjacent changes.
review_rules: []
communication_style: concise
model_config:
  provider: minimax
```

```yaml
# profiles/hermes-database.yaml
id: hermes-database
name: Hermes-Database
type: tactical_worker
version: 1
role_contract: Implement schema, migration, seeding, and data integrity changes.
responsibilities:
  - Migrations, seeders, schema, query integrity, and data safety.
non_responsibilities:
  - UI behavior.
  - Production data writes.
allowed_tools:
  - repo.read_file
  - repo.search
  - repo.apply_patch
  - terminal.run_command
denied_tools:
  - terminal.production_command
  - memory.promote
memory_sources:
  - project_memory
  - run_notes
learning_rules:
  auto_candidate_types:
    - database_fact
confidence_rubric: {}
escalation_rules:
  - Escalate destructive migrations.
review_rules: []
communication_style: concise
model_config:
  provider: minimax
```

```yaml
# profiles/hermes-qa.yaml
id: hermes-qa
name: Hermes-QA
type: qa
version: 1
role_contract: Verify tests, builds, sandbox behavior, and acceptance criteria.
responsibilities:
  - Run tests, lint, builds, sandbox checks, and acceptance criteria verification.
non_responsibilities:
  - Silently patch source code.
allowed_tools:
  - terminal.run_command
  - repo.diff
  - test.run
  - workflow.emit_event
denied_tools:
  - repo.apply_patch
  - memory.promote_governance
memory_sources:
  - project_memory
  - run_notes
learning_rules:
  auto_candidate_types:
    - test_setup_fact
confidence_rubric: {}
escalation_rules:
  - Report verification failures to ProjectManager.
review_rules: []
communication_style: precise
model_config:
  provider: minimax
```

- [ ] **Step 4: Implement profile loader**

Create `src/hermes_core/profiles/loader.py`:

```python
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AgentProfile(BaseModel):
    id: str
    name: str
    type: str
    version: int
    role_contract: str
    responsibilities: list[str]
    non_responsibilities: list[str]
    allowed_tools: list[str]
    denied_tools: list[str]
    memory_sources: list[str]
    learning_rules: dict[str, Any] = Field(default_factory=dict)
    confidence_rubric: dict[str, Any] = Field(default_factory=dict)
    escalation_rules: list[str] = Field(default_factory=list)
    review_rules: list[str] = Field(default_factory=list)
    communication_style: str
    model_config_data: dict[str, Any] = Field(default_factory=dict, alias="model_config")


def load_profile(path: str | Path) -> AgentProfile:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return AgentProfile.model_validate(data)


def load_profiles(directory: str | Path) -> list[AgentProfile]:
    paths = sorted(Path(directory).glob("*.yaml"))
    return [load_profile(path) for path in paths]
```

- [ ] **Step 5: Verify profile tests pass**

Run:

```bash
pytest tests/test_profiles.py -v
```

Expected:

```text
2 passed
```

## Task 4: Runtime Prompt Compiler

**Files:**
- Create: `src/hermes_core/profiles/compiler.py`
- Modify: `tests/test_profiles.py`

- [ ] **Step 1: Add compiler test**

Append to `tests/test_profiles.py`:

```python
from hermes_core.profiles.compiler import compile_runtime_context


def test_compiles_runtime_context_from_profile_and_run_data():
    profile = load_profile("profiles/hermes-backend.yaml")
    context = compile_runtime_context(
        profile=profile,
        workflow_state="implementation_running",
        task_context={
            "ticket": "Fix login validation",
            "allowed_paths": ["backend/app/"],
        },
        memory=[
            "Backend validation errors use ProblemDetails format.",
        ],
        tools=["repo.read_file", "repo.search", "repo.apply_patch"],
    )

    assert "Hermes-Backend" in context
    assert "Fix login validation" in context
    assert "ProblemDetails" in context
    assert "repo.apply_patch" in context
```

- [ ] **Step 2: Implement compiler**

Create `src/hermes_core/profiles/compiler.py`:

```python
from typing import Any

from hermes_core.profiles.loader import AgentProfile


def compile_runtime_context(
    *,
    profile: AgentProfile,
    workflow_state: str,
    task_context: dict[str, Any],
    memory: list[str],
    tools: list[str],
) -> str:
    responsibilities = "\n".join(f"- {item}" for item in profile.responsibilities)
    non_responsibilities = "\n".join(f"- {item}" for item in profile.non_responsibilities)
    memory_lines = "\n".join(f"- {item}" for item in memory) or "- No promoted memory loaded."
    tool_lines = "\n".join(f"- {item}" for item in tools)
    task_lines = "\n".join(f"- {key}: {value}" for key, value in task_context.items())

    return f"""# Agent
Name: {profile.name}
Role: {profile.role_contract}
Workflow state: {workflow_state}

# Responsibilities
{responsibilities}

# Non-Responsibilities
{non_responsibilities}

# Task Context
{task_lines}

# Relevant Memory
{memory_lines}

# Available Tools
{tool_lines}

# Operating Rule
Use only the listed tools. Respect non-responsibilities and escalate when the
task requires denied tools, out-of-scope paths, or high-risk actions.
"""
```

- [ ] **Step 3: Verify profile and compiler tests pass**

Run:

```bash
pytest tests/test_profiles.py -v
```

Expected:

```text
3 passed
```

## Task 5: Run-State Engine

**Files:**
- Create: `src/hermes_core/runs/state.py`
- Create: `src/hermes_core/runs/service.py`
- Modify: `tests/test_runs.py`

- [ ] **Step 1: Add run-state service tests**

Append to `tests/test_runs.py`:

```python
from hermes_core.runs.service import RunService


def test_run_service_creates_and_transitions_run(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)

    service = RunService(session_factory)
    run = service.create_run("new_project_creation", {"project_name": "AeroTrack"})
    assert run.state == "received"

    transitioned = service.transition(run.id, "triaged", {"triage": "accepted"})
    assert transitioned.state == "triaged"
    assert transitioned.payload["project_name"] == "AeroTrack"
    assert transitioned.payload["triage"] == "accepted"
```

- [ ] **Step 2: Implement allowed states**

Create `src/hermes_core/runs/state.py`:

```python
NEW_PROJECT_STATES = {
    "received",
    "triaged",
    "manager_policy_checked",
    "larv_full_session_started",
    "larv_full_waiting_for_input",
    "larv_full_input_received",
    "larv_full_resumed",
    "larv_full_completed",
    "larv_full_interrupted",
    "larv_full_recovery_required",
    "larv_artifacts_ingested",
    "project_context_candidate_created",
    "worker_execution_running",
    "qa_verification_running",
    "final_report_ready",
    "permanent_project_agent_created",
    "learning_candidates_created",
    "completed",
    "failed",
}

ISSUE_FIX_STATES = {
    "received",
    "triaged",
    "mad_confidence_scored",
    "solo_or_assembly_selected",
    "context_oracle_analysis_done",
    "implementation_running",
    "qa_verification_running",
    "project_agent_review_done",
    "manager_audit_done",
    "final_report_ready",
    "awaiting_human_pr_approval",
    "learning_candidates_created",
    "completed",
    "failed",
}


WORKFLOW_STATES = {
    "new_project_creation": NEW_PROJECT_STATES,
    "issue_fix": ISSUE_FIX_STATES,
}
```

- [ ] **Step 3: Implement run service**

Create `src/hermes_core/runs/service.py`:

```python
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from hermes_core.models import Run
from hermes_core.runs.state import WORKFLOW_STATES


class RunService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create_run(self, workflow_type: str, payload: dict[str, Any] | None = None) -> Run:
        if workflow_type not in WORKFLOW_STATES:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

        with self.session_factory() as session:
            run = Run(
                workflow_type=workflow_type,
                state="received",
                payload=payload or {},
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return run

    def transition(self, run_id: int, next_state: str, payload_update: dict[str, Any] | None = None) -> Run:
        with self.session_factory() as session:
            run = session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run not found: {run_id}")
            allowed_states = WORKFLOW_STATES[run.workflow_type]
            if next_state not in allowed_states:
                raise ValueError(f"Invalid state for {run.workflow_type}: {next_state}")
            run.state = next_state
            run.payload = {**(run.payload or {}), **(payload_update or {})}
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
```

- [ ] **Step 4: Verify run-state tests pass**

Run:

```bash
pytest tests/test_runs.py -v
```

Expected:

```text
2 passed
```

## Task 6: Policy and Permission Layer

**Files:**
- Create: `src/hermes_core/policy/rules.py`
- Create: `src/hermes_core/policy/service.py`
- Create: `tests/test_policy.py`

- [ ] **Step 1: Write policy tests**

Create `tests/test_policy.py`:

```python
from hermes_core.policy.service import PolicyRequest, PolicyService


def test_frontend_can_patch_frontend_path():
    service = PolicyService()
    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-frontend",
            workflow_type="issue_fix",
            action="repo.apply_patch",
            target="frontend/src/App.tsx",
            approval_state="project_manager_assigned",
        )
    )
    assert result.decision == "allowed"


def test_frontend_database_patch_requires_escalation():
    service = PolicyService()
    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-frontend",
            workflow_type="issue_fix",
            action="repo.apply_patch",
            target="backend/database/migrations/2026_01_01_create_users.php",
            approval_state="project_manager_assigned",
        )
    )
    assert result.decision == "needs_escalation"


def test_qa_cannot_patch_source():
    service = PolicyService()
    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-qa",
            workflow_type="issue_fix",
            action="repo.apply_patch",
            target="backend/app/Service.php",
            approval_state="qa_verification",
        )
    )
    assert result.decision == "denied"
```

- [ ] **Step 2: Implement policy rules**

Create `src/hermes_core/policy/rules.py`:

```python
HIGH_RISK_TARGET_HINTS = (
    ".env",
    "secrets",
    "auth",
    "payment",
    "billing",
)

AGENT_PATH_SCOPES = {
    "hermes-frontend": ("frontend/", "web/", "resources/js/", "src/"),
    "hermes-backend": ("backend/", "app/", "server/", "api/"),
    "hermes-database": ("database/", "migrations/", "seeders/", "schema/"),
}

DENIED_ACTIONS = {
    "hermes-qa": {"repo.apply_patch"},
}
```

- [ ] **Step 3: Implement policy service**

Create `src/hermes_core/policy/service.py`:

```python
from pydantic import BaseModel

from hermes_core.policy.rules import AGENT_PATH_SCOPES, DENIED_ACTIONS, HIGH_RISK_TARGET_HINTS


class PolicyRequest(BaseModel):
    agent_id: str
    workflow_type: str
    action: str
    target: str
    approval_state: str
    justification: str = ""


class PolicyResult(BaseModel):
    decision: str
    reason: str


class PolicyService:
    def evaluate(self, request: PolicyRequest) -> PolicyResult:
        denied = DENIED_ACTIONS.get(request.agent_id, set())
        if request.action in denied:
            return PolicyResult(decision="denied", reason="Action denied for agent role.")

        target_lower = request.target.lower()
        if any(hint in target_lower for hint in HIGH_RISK_TARGET_HINTS):
            return PolicyResult(decision="needs_escalation", reason="Target matches high-risk path hint.")

        if request.action == "repo.apply_patch":
            scopes = AGENT_PATH_SCOPES.get(request.agent_id)
            if scopes and not request.target.startswith(scopes):
                return PolicyResult(decision="needs_escalation", reason="Target outside agent path scope.")

        return PolicyResult(decision="allowed", reason="Request allowed by current policy.")
```

- [ ] **Step 4: Verify policy tests pass**

Run:

```bash
pytest tests/test_policy.py -v
```

Expected:

```text
3 passed
```

## Task 7: Event and Memory Services

**Files:**
- Create: `src/hermes_core/events/service.py`
- Create: `src/hermes_core/memory/service.py`
- Create: `tests/test_memory.py`

- [ ] **Step 1: Write memory/event tests**

Create `tests/test_memory.py`:

```python
from hermes_core.db import create_session_factory, init_db
from hermes_core.events.service import EventService
from hermes_core.memory.service import MemoryService


def test_event_service_records_event(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = EventService(session_factory)

    event = service.emit("workflow.created", {"workflow_type": "issue_fix"}, run_id=1)

    assert event.id is not None
    assert event.type == "workflow.created"
    assert event.payload["workflow_type"] == "issue_fix"


def test_memory_service_creates_candidate_learning(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = MemoryService(session_factory)

    record = service.create_candidate(
        type="test_setup_fact",
        scope="project",
        summary="Project uses pnpm for frontend tests.",
        details="Observed in package manager files during run.",
        confidence=0.95,
        evidence_refs=["run:1"],
        created_by_agent="hermes-qa",
        source_run_id=1,
    )

    assert record.status == "candidate"
    assert record.confidence == 0.95
```

- [ ] **Step 2: Implement event service**

Create `src/hermes_core/events/service.py`:

```python
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from hermes_core.models import Event


class EventService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def emit(self, type: str, payload: dict[str, Any], run_id: int | None = None) -> Event:
        with self.session_factory() as session:
            event = Event(type=type, payload=payload, run_id=run_id)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
```

- [ ] **Step 3: Implement memory service**

Create `src/hermes_core/memory/service.py`:

```python
from collections.abc import Callable

from sqlalchemy.orm import Session

from hermes_core.models import MemoryRecord


class MemoryService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create_candidate(
        self,
        *,
        type: str,
        scope: str,
        summary: str,
        details: str,
        confidence: float,
        evidence_refs: list[str],
        created_by_agent: str,
        source_run_id: int | None = None,
    ) -> MemoryRecord:
        with self.session_factory() as session:
            record = MemoryRecord(
                type=type,
                scope=scope,
                summary=summary,
                details=details,
                status="candidate",
                confidence=confidence,
                evidence_refs=evidence_refs,
                source_run_id=source_run_id,
                created_by_agent=created_by_agent,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
```

- [ ] **Step 4: Verify memory/event tests pass**

Run:

```bash
pytest tests/test_memory.py -v
```

Expected:

```text
2 passed
```

## Task 8: Execution and LLM Contracts

**Files:**
- Create: `src/hermes_core/execution/contracts.py`
- Create: `src/hermes_core/execution/local.py`
- Create: `src/hermes_core/llm/minimax.py`

- [ ] **Step 1: Implement execution contracts**

Create `src/hermes_core/execution/contracts.py`:

```python
from pydantic import BaseModel


class CommandResult(BaseModel):
    command: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str


class InteractiveSession(BaseModel):
    id: str
    run_id: int
    command: list[str]
    cwd: str
    status: str
```

- [ ] **Step 2: Implement safe local command runner**

Create `src/hermes_core/execution/local.py`:

```python
import subprocess
from pathlib import Path

from hermes_core.execution.contracts import CommandResult


class LocalExecutionAdapter:
    def run_command(self, command: list[str], cwd: str) -> CommandResult:
        result = subprocess.run(
            command,
            cwd=Path(cwd),
            check=False,
            capture_output=True,
            text=True,
        )
        return CommandResult(
            command=command,
            cwd=cwd,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
```

- [ ] **Step 3: Implement MiniMax adapter boundary**

Create `src/hermes_core/llm/minimax.py`:

```python
from pydantic import BaseModel


class LlmMessage(BaseModel):
    role: str
    content: str


class LlmRequest(BaseModel):
    messages: list[LlmMessage]
    model: str


class LlmResponse(BaseModel):
    content: str
    raw: dict


class MiniMaxClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def complete(self, messages: list[LlmMessage]) -> LlmResponse:
        import httpx

        payload = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            response = await client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            raw = response.json()

        content = raw["choices"][0]["message"]["content"]
        return LlmResponse(content=content, raw=raw)
```

- [ ] **Step 4: Verify imports**

Run:

```bash
python - <<'PY'
from hermes_core.execution.local import LocalExecutionAdapter
from hermes_core.llm.minimax import MiniMaxClient
print(LocalExecutionAdapter.__name__, MiniMaxClient.__name__)
PY
```

Expected:

```text
LocalExecutionAdapter MiniMaxClient
```

## Task 9: API and CLI

**Files:**
- Create: `src/hermes_core/app.py`
- Create: `src/hermes_core/api/routes.py`
- Create: `src/hermes_core/cli.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write API test**

Create `tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Implement API routes**

Create `src/hermes_core/api/routes.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 3: Implement app factory**

Create `src/hermes_core/app.py`:

```python
from fastapi import FastAPI

from hermes_core.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Hermes Core")
    app.include_router(router)
    return app


app = create_app()
```

- [ ] **Step 4: Implement CLI**

Create `src/hermes_core/cli.py`:

```python
import typer

from hermes_core.config import get_settings
from hermes_core.db import create_session_factory, init_db

app = typer.Typer()


@app.command()
def init() -> None:
    settings = get_settings()
    engine, _ = create_session_factory(settings.database_url)
    init_db(engine)
    typer.echo("Hermes database initialized.")


@app.command()
def profiles() -> None:
    from hermes_core.profiles.loader import load_profiles

    settings = get_settings()
    loaded = load_profiles(settings.profile_dir)
    for profile in loaded:
        typer.echo(f"{profile.id}: {profile.name}")
```

- [ ] **Step 5: Verify API and CLI**

Run:

```bash
pytest tests/test_api.py -v
hermes-core profiles
```

Expected:

```text
1 passed
hermes-triage: Hermes-Triage
hermes-manager: Hermes-Manager
hermes-project-manager: Hermes-ProjectManager
hermes-frontend: Hermes-Frontend
hermes-backend: Hermes-Backend
hermes-database: Hermes-Database
hermes-qa: Hermes-QA
```

## Task 10: Full Verification

**Files:**
- Modify only if tests or lint reveal concrete issues.

- [ ] **Step 1: Run full test suite**

Run:

```bash
pytest -v
```

Expected:

```text
All tests pass.
```

- [ ] **Step 2: Run lint**

Run:

```bash
ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 3: Confirm documentation still renders**

Run:

```bash
node tools/build-hermes-docs.mjs
```

Expected:

```text
Rendered 10 Markdown files to /home/claude-team/mann/hermes-core/docs/hermes/index.html
```

## Self-Review

Spec coverage:

```text
Agent profiles: Task 3.
Run-state engine: Task 4.
Policy layer: Task 5.
Memory records: Task 6.
Event log: Task 6.
Execution adapter boundary: Task 7.
MiniMax boundary: Task 7.
API/CLI surface: Task 8.
No fake larv:full or issue-fix simulation: preserved. Those are separate vertical plans.
```

Placeholder scan:

```text
No placeholder markers are intentionally present.
The MiniMax adapter performs a real HTTP call through the configured API
boundary.
```

Type consistency:

```text
Run.workflow_type, Run.state, Event.type, MemoryRecord.status, PolicyRequest,
PolicyResult, AgentProfile, and CommandResult names are consistent across tasks.
```
