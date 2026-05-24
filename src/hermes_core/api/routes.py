from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from hermes_core.config import get_settings
from hermes_core.db import create_session_factory, init_db
from hermes_core.profiles.loader import load_profiles
from hermes_core.runs.service import RunService

router = APIRouter()


class CreateRunRequest(BaseModel):
    workflow_type: str
    payload: dict[str, Any] = {}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/profiles")
def profiles() -> dict[str, list[dict[str, Any]]]:
    settings = get_settings()
    loaded = load_profiles(settings.profile_dir)
    return {
        "profiles": [
            {
                "id": profile.id,
                "name": profile.name,
                "type": profile.type,
                "version": profile.version,
            }
            for profile in loaded
        ]
    }


@router.post("/runs")
def create_run(request: CreateRunRequest) -> dict[str, Any]:
    settings = get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    service = RunService(session_factory)
    run = service.create_run(request.workflow_type, request.payload)
    return {
        "id": run.id,
        "workflow_type": run.workflow_type,
        "state": run.state,
        "payload": run.payload,
    }

