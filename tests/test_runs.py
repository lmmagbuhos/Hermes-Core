from hermes_core.db import create_session_factory, init_db
from hermes_core.models import Run
from hermes_core.runs.service import RunService


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
        assert saved is not None
        assert saved.workflow_type == "issue_fix"
        assert saved.state == "received"


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


def test_run_service_rejects_invalid_workflow_state(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)

    service = RunService(session_factory)
    run = service.create_run("issue_fix", {"ticket": "BUG-123"})

    try:
        service.transition(run.id, "larv_full_completed")
    except ValueError as error:
        assert "Invalid state for issue_fix" in str(error)
    else:
        raise AssertionError("Expected invalid state transition to fail")
