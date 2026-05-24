from fastapi import FastAPI

from hermes_core.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Hermes Core")
    app.include_router(router)
    return app


app = create_app()

