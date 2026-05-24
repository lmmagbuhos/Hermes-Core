from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_larv_skill_endpoints_require_shared_token(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    client = TestClient(create_app())

    response = client.post(
        "/workflows/new-project/larv-skill/session-started",
        json={
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(tmp_path),
        },
    )

    assert response.status_code == 401


def test_larv_skill_output_is_idempotent_by_event_id(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    client = TestClient(create_app())
    headers = {"X-Hermes-Token": "secret-token"}
    started = client.post(
        "/workflows/new-project/larv-skill/session-started",
        headers=headers,
        json={
            "event_id": "event-start",
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(tmp_path),
        },
    ).json()
    session_id = started["interactive_session"]["id"]

    first = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/output",
        headers=headers,
        json={
            "event_id": "event-output-1",
            "sequence": 1,
            "stream": "stdout",
            "output": "hello",
        },
    )
    second = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/output",
        headers=headers,
        json={
            "event_id": "event-output-1",
            "sequence": 1,
            "stream": "stdout",
            "output": "hello",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["idempotent_replay"] is True
    transcript = tmp_path / ".hermes" / "transcripts" / "run_1.log"
    assert transcript.read_text(encoding="utf-8") == "hello"


def test_larv_skill_output_rejects_unknown_stream_label(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    client = TestClient(create_app())
    headers = {"X-Hermes-Token": "secret-token"}
    started = client.post(
        "/workflows/new-project/larv-skill/session-started",
        headers=headers,
        json={
            "event_id": "event-start",
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(tmp_path),
        },
    ).json()
    session_id = started["interactive_session"]["id"]

    response = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/output",
        headers=headers,
        json={
            "event_id": "event-output-1",
            "sequence": 1,
            "stream": "system-log",
            "output": "hello",
        },
    )

    assert response.status_code == 422


def test_larv_skill_prompt_shown_records_structured_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    client = TestClient(create_app())
    headers = {"X-Hermes-Token": "secret-token"}
    started = client.post(
        "/workflows/new-project/larv-skill/session-started",
        headers=headers,
        json={
            "event_id": "event-start",
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(tmp_path),
        },
    ).json()
    session_id = started["interactive_session"]["id"]

    first = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/prompt-shown",
        headers=headers,
        json={
            "event_id": "event-prompt-stack",
            "prompt_id": "stack-choice-001",
            "prompt": "Which backend stack should be used?",
            "choices": ["Fastify", "Laravel"],
            "default": "Fastify",
            "is_required": True,
            "metadata": {"source": "larv:full"},
        },
    )
    second = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/prompt-shown",
        headers=headers,
        json={
            "event_id": "event-prompt-stack",
            "prompt_id": "stack-choice-001",
            "prompt": "Which backend stack should be used?",
            "choices": ["Fastify", "Laravel"],
            "default": "Fastify",
            "is_required": True,
            "metadata": {"source": "larv:full"},
        },
    )

    assert first.status_code == 200
    assert first.json()["run"]["state"] == "larv_full_waiting_for_input"
    assert first.json()["interactive_session"]["status"] == "waiting_for_input"
    assert first.json()["interactive_session"]["last_prompt"] == (
        "Which backend stack should be used?"
    )
    assert second.status_code == 200
    assert second.json()["idempotent_replay"] is True


def test_larv_skill_completion_validates_artifact_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    client = TestClient(create_app())
    headers = {"X-Hermes-Token": "secret-token"}
    started = client.post(
        "/workflows/new-project/larv-skill/session-started",
        headers=headers,
        json={
            "event_id": "event-start",
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(tmp_path / "AeroTrack"),
        },
    ).json()
    session_id = started["interactive_session"]["id"]

    response = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/completed",
        headers=headers,
        json={
            "event_id": "event-complete",
            "project_dir": str(tmp_path / "missing"),
        },
    )

    assert response.status_code == 400
    assert "project_dir does not exist" in response.json()["detail"]


def test_larv_skill_failure_endpoint_marks_run_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    client = TestClient(create_app())
    headers = {"X-Hermes-Token": "secret-token"}
    started = client.post(
        "/workflows/new-project/larv-skill/session-started",
        headers=headers,
        json={
            "event_id": "event-start",
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(tmp_path),
        },
    ).json()
    session_id = started["interactive_session"]["id"]

    failed = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/failed",
        headers=headers,
        json={
            "event_id": "event-failed",
            "reason": "larv skill crashed",
        },
    )

    assert failed.status_code == 200
    assert failed.json()["run"]["state"] == "failed"
