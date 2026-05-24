from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_api_starts_new_project_larv_session(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/workflows/new-project/larv-full/start",
        json={
            "project_name": "AeroTrack",
            "command": ["larv:full"],
            "cwd": str(tmp_path),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run"]["state"] == "larv_full_session_started"
    assert body["interactive_session"]["status"] == "running"


def test_api_submits_human_input(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    client = TestClient(create_app())
    started = client.post(
        "/workflows/new-project/larv-full/start",
        json={
            "project_name": "AeroTrack",
            "command": ["larv:full"],
            "cwd": str(tmp_path),
        },
    ).json()
    session_id = started["interactive_session"]["id"]
    client.post(
        f"/interactive-sessions/{session_id}/waiting-for-input",
        json={
            "prompt_id": "stack",
            "prompt": "Choose stack",
        },
    )

    response = client.post(
        f"/interactive-sessions/{session_id}/stdin",
        json={
            "prompt_id": "stack",
            "answer": "Fastify",
        },
    )

    assert response.status_code == 200
    assert response.json()["run"]["state"] == "larv_full_input_received"
