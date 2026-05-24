import json

import httpx
import pytest

from hermes_core.integrations.dtt_ai import DttAiEventIdFactory, DttAiHermesClient


def test_event_id_factory_formats_stable_ids():
    event_ids = DttAiEventIdFactory("dtt-session-123")

    assert event_ids.session_started() == "dtt-session-123-started"
    assert event_ids.output(7) == "dtt-session-123-output-000007"
    assert event_ids.prompt_shown("stack") == "dtt-session-123-prompt-stack"
    assert event_ids.human_answer("stack") == "dtt-session-123-answer-stack"
    assert event_ids.completed() == "dtt-session-123-completed"
    assert event_ids.failed() == "dtt-session-123-failed"


def test_client_sends_auth_header_and_larv_payloads():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request, json.loads(request.content.decode("utf-8"))))
        if request.url.path.endswith("/session-started"):
            return httpx.Response(
                200,
                json={
                    "run": {"id": 4, "state": "larv_full_session_started"},
                    "interactive_session": {"id": "sess_123", "run_id": 4},
                },
            )
        return httpx.Response(
            200,
            json={
                "run": {"id": 4, "state": "ok"},
                "interactive_session": {"id": "sess_123", "run_id": 4},
            },
        )

    http_client = httpx.Client(base_url="http://testserver", transport=httpx.MockTransport(handler))
    client = DttAiHermesClient(
        base_url="http://unused",
        token="secret-token",
        event_ids=DttAiEventIdFactory("dtt-session-123"),
        http_client=http_client,
    )

    session = client.start_larv_skill_session(
        project_name="AeroTrack",
        external_session_id="dtt-session-123",
        cwd="/srv/dtt-ai/AeroTrack",
    )
    client.record_output(
        session_id=session.id,
        sequence=1,
        stream="stdout",
        output="Choose stack",
    )
    client.record_prompt_shown(
        session_id=session.id,
        prompt_id="stack",
        prompt="Choose stack",
        choices=["Fastify", "Laravel"],
        default="Fastify",
        metadata={"source": "larv:full"},
    )
    client.record_human_answer(session_id=session.id, prompt_id="stack", answer="Fastify")
    client.complete_session(session_id=session.id, project_dir="/srv/dtt-ai/AeroTrack")

    assert session.id == "sess_123"
    assert session.run_id == 4
    assert all(request.headers["X-Hermes-Token"] == "secret-token" for request, _ in requests)
    assert [request.url.path for request, _body in requests] == [
        "/workflows/new-project/larv-skill/session-started",
        "/workflows/new-project/larv-skill/sess_123/output",
        "/workflows/new-project/larv-skill/sess_123/prompt-shown",
        "/workflows/new-project/larv-skill/sess_123/human-answer",
        "/workflows/new-project/larv-skill/sess_123/completed",
    ]
    assert requests[0][1]["event_id"] == "dtt-session-123-started"
    assert requests[1][1]["event_id"] == "dtt-session-123-output-000001"
    assert requests[2][1]["event_id"] == "dtt-session-123-prompt-stack"
    assert requests[3][1]["event_id"] == "dtt-session-123-answer-stack"
    assert requests[4][1]["event_id"] == "dtt-session-123-completed"


def test_client_raises_for_hermes_error_response():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Invalid token"})

    http_client = httpx.Client(base_url="http://testserver", transport=httpx.MockTransport(handler))
    client = DttAiHermesClient(
        base_url="http://unused",
        event_ids=DttAiEventIdFactory("dtt-session-123"),
        http_client=http_client,
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.start_larv_skill_session(
            project_name="AeroTrack",
            external_session_id="dtt-session-123",
            cwd="/srv/dtt-ai/AeroTrack",
        )
