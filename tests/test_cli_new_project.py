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
