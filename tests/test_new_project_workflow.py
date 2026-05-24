from hermes_core.db import create_session_factory, init_db
from hermes_core.models import Event, ProjectContextCandidate
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
