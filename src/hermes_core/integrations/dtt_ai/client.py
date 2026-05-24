from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

StreamLabel = Literal["stdout", "stderr", "agent"]


@dataclass(frozen=True)
class DttAiSession:
    id: str
    run_id: int
    raw_response: dict[str, Any]


@dataclass(frozen=True)
class DttAiEventIdFactory:
    prefix: str

    def session_started(self) -> str:
        return f"{self.prefix}-started"

    def output(self, sequence: int) -> str:
        return f"{self.prefix}-output-{sequence:06d}"

    def prompt_shown(self, prompt_id: str) -> str:
        return f"{self.prefix}-prompt-{prompt_id}"

    def human_answer(self, prompt_id: str) -> str:
        return f"{self.prefix}-answer-{prompt_id}"

    def completed(self) -> str:
        return f"{self.prefix}-completed"

    def failed(self) -> str:
        return f"{self.prefix}-failed"


class DttAiHermesClient:
    def __init__(
        self,
        *,
        base_url: str,
        token: str = "",
        timeout: float = 10.0,
        event_ids: DttAiEventIdFactory,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.event_ids = event_ids
        self._owns_client = http_client is None
        headers = self._headers(token)
        if http_client is not None:
            http_client.headers.update(headers)
            self._client = http_client
        else:
            self._client = httpx.Client(
                base_url=base_url,
                headers=headers,
                timeout=timeout,
            )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> DttAiHermesClient:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def start_larv_skill_session(
        self,
        *,
        project_name: str,
        external_session_id: str,
        cwd: str,
    ) -> DttAiSession:
        response = self._post(
            "/workflows/new-project/larv-skill/session-started",
            {
                "event_id": self.event_ids.session_started(),
                "project_name": project_name,
                "external_session_id": external_session_id,
                "cwd": cwd,
            },
        )
        interactive_session = response["interactive_session"]
        return DttAiSession(
            id=interactive_session["id"],
            run_id=interactive_session["run_id"],
            raw_response=response,
        )

    def record_output(
        self,
        *,
        session_id: str,
        output: str,
        sequence: int,
        stream: StreamLabel = "stdout",
    ) -> dict[str, Any]:
        return self._post(
            f"/workflows/new-project/larv-skill/{session_id}/output",
            {
                "event_id": self.event_ids.output(sequence),
                "sequence": sequence,
                "stream": stream,
                "output": output,
            },
        )

    def record_prompt_shown(
        self,
        *,
        session_id: str,
        prompt_id: str,
        prompt: str,
        choices: list[str] | None = None,
        default: str | None = None,
        is_required: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            f"/workflows/new-project/larv-skill/{session_id}/prompt-shown",
            {
                "event_id": self.event_ids.prompt_shown(prompt_id),
                "prompt_id": prompt_id,
                "prompt": prompt,
                "choices": choices or [],
                "default": default,
                "is_required": is_required,
                "metadata": metadata or {},
            },
        )

    def record_human_answer(
        self,
        *,
        session_id: str,
        prompt_id: str,
        answer: str,
    ) -> dict[str, Any]:
        return self._post(
            f"/workflows/new-project/larv-skill/{session_id}/human-answer",
            {
                "event_id": self.event_ids.human_answer(prompt_id),
                "prompt_id": prompt_id,
                "answer": answer,
            },
        )

    def complete_session(self, *, session_id: str, project_dir: str) -> dict[str, Any]:
        return self._post(
            f"/workflows/new-project/larv-skill/{session_id}/completed",
            {
                "event_id": self.event_ids.completed(),
                "project_dir": project_dir,
            },
        )

    def fail_session(self, *, session_id: str, reason: str) -> dict[str, Any]:
        return self._post(
            f"/workflows/new-project/larv-skill/{session_id}/failed",
            {
                "event_id": self.event_ids.failed(),
                "reason": reason,
            },
        )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(path, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        if not token:
            return {}
        return {"X-Hermes-Token": token}
