from hermes_core.db import create_session_factory, init_db
from hermes_core.runtime.interactive import InteractiveRuntime
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
