from hermes_core.db import create_session_factory, init_db
from hermes_core.models import Event, ProjectContextCandidate
from hermes_core.workflows.new_project import NewProjectWorkflowService


def test_records_external_larv_skill_session_and_output(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = NewProjectWorkflowService(session_factory)

    result = service.record_larv_skill_session_started(
        project_name="AeroTrack",
        external_session_id="dtt-session-123",
        cwd=str(tmp_path),
    )
    output = service.record_larv_skill_output(
        result.interactive_session.id,
        output="larv:full asked: Which stack?",
    )

    assert output.interactive_session.status == "running"
    assert output.run.state == "larv_full_session_started"
    transcript = tmp_path / ".hermes" / "transcripts" / "run_1.log"
    assert transcript.read_text(encoding="utf-8") == "larv:full asked: Which stack?"

    with session_factory() as db:
        event_types = [event.type for event in db.query(Event).order_by(Event.id).all()]
    assert "larv.skill_session_started" in event_types
    assert "terminal.stdout" in event_types


def test_records_external_larv_human_answer_without_pty_write(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = NewProjectWorkflowService(session_factory)
    result = service.record_larv_skill_session_started(
        project_name="AeroTrack",
        external_session_id="dtt-session-123",
        cwd=str(tmp_path),
    )

    answered = service.record_larv_skill_human_answer(
        result.interactive_session.id,
        prompt_id="stack",
        answer="Fastify and Next.js",
    )

    assert answered.run.state == "larv_full_input_received"
    assert answered.interactive_session.stdin_history == [
        {
            "prompt_id": "stack",
            "answer": "Fastify and Next.js",
        }
    ]


def test_completes_external_larv_skill_session_and_creates_candidate(tmp_path):
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
    result = service.record_larv_skill_session_started(
        project_name="AeroTrack",
        external_session_id="dtt-session-123",
        cwd=str(project),
    )
    service.record_larv_skill_output(result.interactive_session.id, output="Human chose stack.")

    completed = service.complete_external_larv_skill_session(
        result.interactive_session.id,
        project_dir=project,
    )

    assert completed.run.state == "project_context_candidate_created"
    with session_factory() as db:
        candidate = db.query(ProjectContextCandidate).one()
    assert candidate.project_name == "AeroTrack"
    assert candidate.blueprint["package_manager"] == "pnpm"
