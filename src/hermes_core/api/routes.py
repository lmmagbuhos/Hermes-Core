from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from hermes_core.config import get_settings
from hermes_core.db import create_session_factory, init_db
from hermes_core.profiles.loader import load_profiles
from hermes_core.runs.service import RunService
from hermes_core.workflows.new_project import NewProjectWorkflowResult, NewProjectWorkflowService

router = APIRouter()


class CreateRunRequest(BaseModel):
    workflow_type: str
    payload: dict[str, Any] = {}


class StartLarvFullRequest(BaseModel):
    project_name: str
    command: list[str]
    cwd: str


class WaitingForInputRequest(BaseModel):
    prompt_id: str
    prompt: str


class SubmitInputRequest(BaseModel):
    prompt_id: str
    answer: str


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


def _workflow_service() -> NewProjectWorkflowService:
    settings = get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    return NewProjectWorkflowService(session_factory)


def _workflow_result_payload(result: NewProjectWorkflowResult) -> dict[str, Any]:
    return {
        "run": {
            "id": result.run.id,
            "workflow_type": result.run.workflow_type,
            "state": result.run.state,
            "payload": result.run.payload,
        },
        "interactive_session": {
            "id": result.interactive_session.id,
            "run_id": result.interactive_session.run_id,
            "command": result.interactive_session.command,
            "cwd": result.interactive_session.cwd,
            "status": result.interactive_session.status,
            "last_prompt": result.interactive_session.last_prompt,
            "transcript_ref": result.interactive_session.transcript_ref,
        },
    }


@router.post("/workflows/new-project/larv-full/start")
def start_larv_full(request: StartLarvFullRequest) -> dict[str, Any]:
    service = _workflow_service()
    result = service.start_larv_full(
        project_name=request.project_name,
        command=request.command,
        cwd=request.cwd,
    )
    return _workflow_result_payload(result)


@router.post("/interactive-sessions/{session_id}/waiting-for-input")
def mark_waiting_for_input(
    session_id: str,
    request: WaitingForInputRequest,
) -> dict[str, Any]:
    service = _workflow_service()
    result = service.waiting_for_input(
        session_id,
        prompt_id=request.prompt_id,
        prompt=request.prompt,
    )
    return _workflow_result_payload(result)


@router.post("/interactive-sessions/{session_id}/stdin")
def submit_stdin(session_id: str, request: SubmitInputRequest) -> dict[str, Any]:
    service = _workflow_service()
    result = service.submit_human_input(
        session_id,
        prompt_id=request.prompt_id,
        answer=request.answer,
    )
    return _workflow_result_payload(result)
