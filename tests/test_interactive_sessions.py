from hermes_core.db import create_session_factory, init_db
from hermes_core.execution.interactive import PtyInteractiveRunner
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
