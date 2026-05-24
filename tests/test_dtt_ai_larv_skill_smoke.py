import importlib.util
from pathlib import Path

import httpx


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "tools" / "dtt_ai_larv_skill_smoke.py"
SPEC = importlib.util.spec_from_file_location("dtt_ai_larv_skill_smoke", SCRIPT_PATH)
assert SPEC is not None
smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(smoke)


def test_reference_client_completed_flow_contract(tmp_path):
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json_body(request)
        requests.append((request.url.path, body))
        if request.url.path.endswith("/session-started"):
            return httpx.Response(
                200,
                json={
                    "run": {"state": "larv_full_session_started"},
                    "interactive_session": {"id": "sess_complete"},
                },
            )
        if request.url.path.endswith("/prompt-shown"):
            return httpx.Response(
                200,
                json={
                    "run": {"state": "larv_full_waiting_for_input"},
                    "interactive_session": {"id": "sess_complete"},
                },
            )
        if request.url.path.endswith("/human-answer"):
            return httpx.Response(
                200,
                json={
                    "run": {"state": "larv_full_input_received"},
                    "interactive_session": {"id": "sess_complete"},
                },
            )
        if request.url.path.endswith("/completed"):
            return httpx.Response(
                200,
                json={
                    "run": {"state": "project_context_candidate_created"},
                    "interactive_session": {"id": "sess_complete"},
                },
            )
        return httpx.Response(
            200,
            json={
                "run": {"state": "larv_full_session_started"},
                "interactive_session": {"id": "sess_complete"},
            },
        )

    client = httpx.Client(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )
    project_dir = tmp_path / "AeroTrack"
    smoke.ensure_minimal_artifacts(project_dir)

    summary = smoke.run_completed_flow(
        client=client,
        event_prefix="event",
        project_name="AeroTrack",
        external_session_id="dtt-session",
        project_dir=str(project_dir),
    )

    assert summary["final_state"] == "project_context_candidate_created"
    assert [path for path, _body in requests] == [
        "/workflows/new-project/larv-skill/session-started",
        "/workflows/new-project/larv-skill/sess_complete/output",
        "/workflows/new-project/larv-skill/sess_complete/prompt-shown",
        "/workflows/new-project/larv-skill/sess_complete/human-answer",
        "/workflows/new-project/larv-skill/sess_complete/completed",
    ]
    prompt_body = requests[2][1]
    assert prompt_body["prompt_id"] == "stack-choice-001"
    assert prompt_body["choices"] == ["Fastify", "Laravel"]
    assert prompt_body["metadata"]["source"] == "larv:full"


def test_reference_client_failed_flow_contract():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json_body(request)
        requests.append((request.url.path, body))
        if request.url.path.endswith("/session-started"):
            return httpx.Response(
                200,
                json={
                    "run": {"state": "larv_full_session_started"},
                    "interactive_session": {"id": "sess_failed"},
                },
            )
        return httpx.Response(
            200,
            json={
                "run": {"state": "failed"},
                "interactive_session": {"id": "sess_failed", "status": "recovery_required"},
            },
        )

    client = httpx.Client(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )

    summary = smoke.run_failed_flow(
        client=client,
        event_prefix="event",
        project_name="AeroTrack",
        cwd="/tmp/AeroTrack",
        external_session_id="dtt-session",
    )

    assert summary == {
        "flow": "failed",
        "session_id": "sess_failed",
        "final_state": "failed",
        "session_status": "recovery_required",
    }
    assert [path for path, _body in requests] == [
        "/workflows/new-project/larv-skill/session-started",
        "/workflows/new-project/larv-skill/sess_failed/failed",
    ]


def json_body(request: httpx.Request) -> dict:
    return smoke.json.loads(request.content.decode("utf-8"))
