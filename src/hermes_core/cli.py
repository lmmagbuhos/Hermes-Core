import typer

from hermes_core.config import get_settings
from hermes_core.db import create_session_factory, init_db
from hermes_core.workflows.new_project import NewProjectWorkflowService

app = typer.Typer()


@app.command()
def init() -> None:
    settings = get_settings()
    engine, _ = create_session_factory(settings.database_url)
    init_db(engine)
    typer.echo("Hermes database initialized.")


@app.command()
def profiles() -> None:
    from hermes_core.profiles.loader import load_profiles

    settings = get_settings()
    loaded = load_profiles(settings.profile_dir)
    for profile in loaded:
        typer.echo(f"{profile.id}: {profile.name}")


def _new_project_service() -> NewProjectWorkflowService:
    settings = get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    return NewProjectWorkflowService(session_factory)


@app.command("new-project-start")
def new_project_start(
    project_name: str,
    cwd: str = typer.Option(...),
    command: list[str] = typer.Option(...),
) -> None:
    service = _new_project_service()
    result = service.start_larv_full(project_name=project_name, command=command, cwd=cwd)
    typer.echo(f"run_id={result.run.id} session_id={result.interactive_session.id}")


@app.command("session-waiting")
def session_waiting(session_id: str, prompt_id: str, prompt: str) -> None:
    service = _new_project_service()
    result = service.waiting_for_input(session_id, prompt_id=prompt_id, prompt=prompt)
    typer.echo(f"run_id={result.run.id} state={result.run.state}")


@app.command("session-input")
def session_input(session_id: str, prompt_id: str, answer: str) -> None:
    service = _new_project_service()
    result = service.submit_human_input(session_id, prompt_id=prompt_id, answer=answer)
    typer.echo(f"run_id={result.run.id} state={result.run.state}")


@app.command("session-output")
def session_output(session_id: str, timeout: float = 0.2) -> None:
    service = _new_project_service()
    result = service.read_interactive_output(session_id, timeout=timeout)
    typer.echo(f"session_id={result.session_id} status={result.status} prompt_id={result.prompt_id}")
    if result.output:
        typer.echo(result.output)
