import typer

from hermes_core.config import get_settings
from hermes_core.db import create_session_factory, init_db

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
