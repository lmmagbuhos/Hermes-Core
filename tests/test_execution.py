from hermes_core.execution.contracts import InteractiveSession
from hermes_core.execution.local import LocalExecutionAdapter


def test_local_execution_adapter_runs_command(tmp_path):
    adapter = LocalExecutionAdapter()

    result = adapter.run_command(["python3", "-c", "print('hermes')"], cwd=str(tmp_path))

    assert result.command == ["python3", "-c", "print('hermes')"]
    assert result.cwd == str(tmp_path)
    assert result.exit_code == 0
    assert result.stdout.strip() == "hermes"
    assert result.stderr == ""


def test_local_execution_adapter_captures_failed_command(tmp_path):
    adapter = LocalExecutionAdapter()

    result = adapter.run_command(
        ["python3", "-c", "import sys; print('bad', file=sys.stderr); sys.exit(7)"],
        cwd=str(tmp_path),
    )

    assert result.exit_code == 7
    assert result.stderr.strip() == "bad"


def test_interactive_session_contract_tracks_larv_full_wait_state():
    session = InteractiveSession(
        id="sess_123",
        run_id=42,
        command=["larv:full"],
        cwd="/workspace/aerotrack",
        status="waiting_for_input",
        transcript_ref="transcripts/sess_123.log",
        last_prompt="Which frontend stack should be used?",
    )

    assert session.id == "sess_123"
    assert session.status == "waiting_for_input"
    assert session.last_prompt == "Which frontend stack should be used?"
