from typer.testing import CliRunner

from hermes_core.cli import app


def test_cli_runtime_read_reports_recovery_for_non_live_session(tmp_path, monkeypatch):
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

    result = runner.invoke(app, ["session-output", session_id])

    assert result.exit_code == 0
    assert "status=recovery_required" in result.stdout
