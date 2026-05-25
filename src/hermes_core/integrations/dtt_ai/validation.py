from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from hermes_core.integrations.dtt_ai.client import DttAiEventIdFactory, DttAiHermesClient


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    ok: bool
    detail: str
    data: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "ok": self.ok,
            "detail": self.detail,
        }
        if self.data:
            payload["data"] = self.data
        return payload


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    checks: list[ValidationCheck]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [check.as_dict() for check in self.checks],
        }


def validate_dtt_ai_environment(
    *,
    hermes_url: str,
    token: str = "",
    workspace_path: str,
    project_name: str = "HermesDttValidation",
    timeout: float = 10.0,
) -> ValidationReport:
    checks: list[ValidationCheck] = []
    workspace = Path(workspace_path).expanduser().resolve()
    event_prefix = f"dtt-env-validation-{uuid4().hex}"

    checks.append(_validate_workspace_path(workspace))
    checks.append(_validate_hermes_health(hermes_url=hermes_url, timeout=timeout))
    if not all(check.ok for check in checks):
        return ValidationReport(ok=False, checks=checks)

    project_dir = workspace / project_name
    _ensure_validation_artifacts(project_dir)

    with DttAiHermesClient(
        base_url=hermes_url,
        token=token,
        timeout=timeout,
        event_ids=DttAiEventIdFactory(event_prefix),
    ) as client:
        checks.append(
            _validate_completion_flow(
                client=client,
                event_ids=DttAiEventIdFactory(f"{event_prefix}-complete"),
                project_name=project_name,
                project_dir=project_dir,
            )
        )
        checks.append(
            _validate_failure_flow(
                client=client,
                event_ids=DttAiEventIdFactory(f"{event_prefix}-failed"),
                project_name=project_name,
                workspace=workspace,
            )
        )

    return ValidationReport(ok=all(check.ok for check in checks), checks=checks)


def _validate_workspace_path(workspace: Path) -> ValidationCheck:
    if not workspace.exists():
        return ValidationCheck(
            name="workspace_path",
            ok=False,
            detail=f"Workspace path does not exist: {workspace}",
        )
    if not workspace.is_dir():
        return ValidationCheck(
            name="workspace_path",
            ok=False,
            detail=f"Workspace path is not a directory: {workspace}",
        )
    probe = workspace / f".hermes_read_probe_{uuid4().hex}"
    try:
        probe.write_text("ok", encoding="utf-8")
        if probe.read_text(encoding="utf-8") != "ok":
            return ValidationCheck(
                name="workspace_path",
                ok=False,
                detail=f"Workspace probe readback failed: {workspace}",
            )
    except OSError as error:
        return ValidationCheck(
            name="workspace_path",
            ok=False,
            detail=f"Workspace is not readable/writable by this process: {error}",
        )
    finally:
        probe.unlink(missing_ok=True)
    return ValidationCheck(
        name="workspace_path",
        ok=True,
        detail=f"Workspace path is readable and writable: {workspace}",
        data={"workspace_path": str(workspace)},
    )


def _validate_hermes_health(*, hermes_url: str, timeout: float) -> ValidationCheck:
    try:
        response = httpx.get(f"{hermes_url.rstrip('/')}/health", timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        return ValidationCheck(
            name="hermes_health",
            ok=False,
            detail=f"Hermes health check failed: {error}",
        )
    if payload.get("status") != "ok":
        return ValidationCheck(
            name="hermes_health",
            ok=False,
            detail=f"Hermes health check returned unexpected payload: {payload}",
        )
    return ValidationCheck(
        name="hermes_health",
        ok=True,
        detail="Hermes health endpoint is reachable.",
        data={"hermes_url": hermes_url},
    )


def _validate_completion_flow(
    *,
    client: DttAiHermesClient,
    event_ids: DttAiEventIdFactory,
    project_name: str,
    project_dir: Path,
) -> ValidationCheck:
    client.event_ids = event_ids
    try:
        session = client.start_larv_skill_session(
            project_name=project_name,
            external_session_id=event_ids.prefix,
            cwd=str(project_dir),
        )
        client.record_output(
            session_id=session.id,
            sequence=1,
            stream="stdout",
            output="Hermes DTT-AI environment validation output.",
        )
        client.record_prompt_shown(
            session_id=session.id,
            prompt_id="validation-prompt",
            prompt="Validation prompt",
            choices=["continue"],
            default="continue",
            metadata={"source": "environment-validation"},
        )
        client.record_human_answer(
            session_id=session.id,
            prompt_id="validation-prompt",
            answer="continue",
        )
        completed = client.complete_session(session_id=session.id, project_dir=str(project_dir))
    except httpx.HTTPStatusError as error:
        return ValidationCheck(
            name="completion_flow",
            ok=False,
            detail=f"Hermes completion flow rejected the request: {error.response.text}",
        )
    except httpx.HTTPError as error:
        return ValidationCheck(
            name="completion_flow",
            ok=False,
            detail=f"Hermes completion flow failed: {error}",
        )
    state = completed["run"]["state"]
    return ValidationCheck(
        name="completion_flow",
        ok=state == "project_context_candidate_created",
        detail=f"Completion flow ended in state: {state}",
        data={"session_id": session.id, "project_dir": str(project_dir)},
    )


def _validate_failure_flow(
    *,
    client: DttAiHermesClient,
    event_ids: DttAiEventIdFactory,
    project_name: str,
    workspace: Path,
) -> ValidationCheck:
    client.event_ids = event_ids
    try:
        session = client.start_larv_skill_session(
            project_name=project_name,
            external_session_id=event_ids.prefix,
            cwd=str(workspace),
        )
        failed = client.fail_session(
            session_id=session.id,
            reason="Hermes DTT-AI environment validation simulated failure.",
        )
    except httpx.HTTPStatusError as error:
        return ValidationCheck(
            name="failure_flow",
            ok=False,
            detail=f"Hermes failure flow rejected the request: {error.response.text}",
        )
    except httpx.HTTPError as error:
        return ValidationCheck(
            name="failure_flow",
            ok=False,
            detail=f"Hermes failure flow failed: {error}",
        )
    state = failed["run"]["state"]
    status = failed["interactive_session"]["status"]
    return ValidationCheck(
        name="failure_flow",
        ok=state == "failed" and status == "recovery_required",
        detail=f"Failure flow ended in state={state}, status={status}",
        data={"session_id": session.id},
    )


def _ensure_validation_artifacts(project_dir: Path) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    package_json = project_dir / "package.json"
    if not package_json.exists():
        package_json.write_text('{"packageManager":"pnpm@9.0.0"}\n', encoding="utf-8")
