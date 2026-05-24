from typer.testing import CliRunner

from hermes_core.cli import app


def test_cli_lists_profiles():
    runner = CliRunner()

    result = runner.invoke(app, ["profiles"])

    assert result.exit_code == 0
    assert "hermes-triage: Hermes-Triage" in result.stdout
    assert "hermes-backend: Hermes-Backend" in result.stdout


def test_cli_initializes_database(tmp_path, monkeypatch):
    db_path = tmp_path / "hermes.db"
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{db_path}")
    runner = CliRunner()

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Hermes database initialized." in result.stdout
    assert db_path.exists()
