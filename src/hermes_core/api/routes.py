from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from hermes_core.config import get_settings
from hermes_core.db import create_session_factory, init_db
from hermes_core.idempotency.service import IdempotencyService
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
    start_process: bool = False


class WaitingForInputRequest(BaseModel):
    prompt_id: str
    prompt: str


class SubmitInputRequest(BaseModel):
    prompt_id: str
    answer: str


class LarvSkillSessionStartedRequest(BaseModel):
    event_id: str | None = None
    project_name: str
    external_session_id: str
    cwd: str


class LarvSkillOutputRequest(BaseModel):
    event_id: str | None = None
    sequence: int | None = None
    stream: Literal["stdout", "stderr", "agent"] = "agent"
    output: str


class LarvSkillHumanAnswerRequest(BaseModel):
    event_id: str | None = None
    prompt_id: str
    answer: str


class LarvSkillCompletedRequest(BaseModel):
    event_id: str | None = None
    project_dir: str


class LarvSkillFailedRequest(BaseModel):
    event_id: str | None = None
    reason: str


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


_WORKFLOW_SERVICE: NewProjectWorkflowService | None = None
_WORKFLOW_DATABASE_URL: str | None = None


def _workflow_service() -> NewProjectWorkflowService:
    global _WORKFLOW_DATABASE_URL, _WORKFLOW_SERVICE
    settings = get_settings()
    if _WORKFLOW_SERVICE is not None and _WORKFLOW_DATABASE_URL == settings.database_url:
        return _WORKFLOW_SERVICE
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    _WORKFLOW_DATABASE_URL = settings.database_url
    _WORKFLOW_SERVICE = NewProjectWorkflowService(session_factory)
    return _WORKFLOW_SERVICE


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


def _idempotency_service() -> IdempotencyService:
    settings = get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    init_db(engine)
    return IdempotencyService(session_factory)


def _require_dtt_ai_token(x_hermes_token: str | None) -> None:
    settings = get_settings()
    if not settings.dtt_ai_shared_token:
        return
    if x_hermes_token != settings.dtt_ai_shared_token:
        raise HTTPException(status_code=401, detail="Invalid or missing Hermes shared token")


def _idempotent_replay(event_id: str | None) -> dict[str, Any] | None:
    if not event_id:
        return None
    existing = _idempotency_service().get(event_id)
    if existing is None:
        return None
    payload = dict(existing.response_payload)
    payload["idempotent_replay"] = True
    return payload


def _record_idempotency(
    *,
    event_id: str | None,
    endpoint: str,
    payload: dict[str, Any],
    run_id: int | None,
) -> None:
    if not event_id:
        return
    _idempotency_service().record(
        event_id=event_id,
        endpoint=endpoint,
        response_payload=payload,
        run_id=run_id,
    )


@router.post("/workflows/new-project/larv-full/start")
def start_larv_full(request: StartLarvFullRequest) -> dict[str, Any]:
    service = _workflow_service()
    result = service.start_larv_full(
        project_name=request.project_name,
        command=request.command,
        cwd=request.cwd,
        start_process=request.start_process,
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


@router.get("/interactive-sessions/{session_id}/output")
def read_interactive_output(session_id: str, timeout: float = 0.2) -> dict[str, Any]:
    service = _workflow_service()
    result = service.read_interactive_output(session_id, timeout=timeout)
    return {
        "session_id": result.session_id,
        "output": result.output,
        "status": result.status,
        "prompt_id": result.prompt_id,
    }


@router.post("/workflows/new-project/larv-skill/session-started")
def record_larv_skill_session_started(
    request: LarvSkillSessionStartedRequest,
    x_hermes_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_dtt_ai_token(x_hermes_token)
    if replay := _idempotent_replay(request.event_id):
        return replay
    service = _workflow_service()
    result = service.record_larv_skill_session_started(
        project_name=request.project_name,
        external_session_id=request.external_session_id,
        cwd=request.cwd,
    )
    payload = _workflow_result_payload(result)
    payload["idempotent_replay"] = False
    _record_idempotency(
        event_id=request.event_id,
        endpoint="larv-skill/session-started",
        payload=payload,
        run_id=result.run.id,
    )
    return payload


@router.post("/workflows/new-project/larv-skill/{session_id}/output")
def record_larv_skill_output(
    session_id: str,
    request: LarvSkillOutputRequest,
    x_hermes_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_dtt_ai_token(x_hermes_token)
    if replay := _idempotent_replay(request.event_id):
        return replay
    service = _workflow_service()
    result = service.record_larv_skill_output(
        session_id,
        output=request.output,
        stream=request.stream,
        sequence=request.sequence,
    )
    payload = _workflow_result_payload(result)
    payload["idempotent_replay"] = False
    _record_idempotency(
        event_id=request.event_id,
        endpoint="larv-skill/output",
        payload=payload,
        run_id=result.run.id,
    )
    return payload


@router.post("/workflows/new-project/larv-skill/{session_id}/human-answer")
def record_larv_skill_human_answer(
    session_id: str,
    request: LarvSkillHumanAnswerRequest,
    x_hermes_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_dtt_ai_token(x_hermes_token)
    if replay := _idempotent_replay(request.event_id):
        return replay
    service = _workflow_service()
    result = service.record_larv_skill_human_answer(
        session_id,
        prompt_id=request.prompt_id,
        answer=request.answer,
    )
    payload = _workflow_result_payload(result)
    payload["idempotent_replay"] = False
    _record_idempotency(
        event_id=request.event_id,
        endpoint="larv-skill/human-answer",
        payload=payload,
        run_id=result.run.id,
    )
    return payload


@router.post("/workflows/new-project/larv-skill/{session_id}/completed")
def complete_larv_skill_session(
    session_id: str,
    request: LarvSkillCompletedRequest,
    x_hermes_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_dtt_ai_token(x_hermes_token)
    if replay := _idempotent_replay(request.event_id):
        return replay
    service = _workflow_service()
    try:
        result = service.complete_external_larv_skill_session(
            session_id,
            project_dir=Path(request.project_dir),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    payload = _workflow_result_payload(result)
    payload["idempotent_replay"] = False
    _record_idempotency(
        event_id=request.event_id,
        endpoint="larv-skill/completed",
        payload=payload,
        run_id=result.run.id,
    )
    return payload


@router.post("/workflows/new-project/larv-skill/{session_id}/failed")
def fail_larv_skill_session(
    session_id: str,
    request: LarvSkillFailedRequest,
    x_hermes_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_dtt_ai_token(x_hermes_token)
    if replay := _idempotent_replay(request.event_id):
        return replay
    service = _workflow_service()
    result = service.record_larv_skill_failed(session_id, reason=request.reason)
    payload = _workflow_result_payload(result)
    payload["idempotent_replay"] = False
    _record_idempotency(
        event_id=request.event_id,
        endpoint="larv-skill/failed",
        payload=payload,
        run_id=result.run.id,
    )
    return payload
