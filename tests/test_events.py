from hermes_core.db import create_session_factory, init_db
from hermes_core.events.service import EventService
from hermes_core.models import Event
from hermes_core.runs.service import RunService


def test_event_service_records_event(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = EventService(session_factory)

    event = service.emit("workflow.created", {"workflow_type": "issue_fix"}, run_id=1)

    assert event.id is not None
    assert event.type == "workflow.created"
    assert event.run_id == 1
    assert event.payload["workflow_type"] == "issue_fix"


def test_run_service_emits_workflow_events(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)

    service = RunService(session_factory)
    run = service.create_run("issue_fix", {"ticket": "BUG-123"})
    service.transition(run.id, "triaged", {"triage": "accepted"})

    with session_factory() as session:
        events = session.query(Event).order_by(Event.id).all()

    assert [event.type for event in events] == [
        "workflow.created",
        "workflow.state_changed",
    ]
    assert events[0].payload["workflow_type"] == "issue_fix"
    assert events[1].payload["from_state"] == "received"
    assert events[1].payload["to_state"] == "triaged"
