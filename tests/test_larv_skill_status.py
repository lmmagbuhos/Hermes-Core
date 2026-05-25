from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_larv_skill_status_reports_prompt_and_events(tmp_path, monkeypatch):
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
    client.post(
        f"/workflows/new-project/larv-skill/{session_id}/prompt-shown",
        headers=headers,
        json={
            "event_id": "event-prompt",
            "prompt_id": "stack",
            "prompt": "Choose stack",
            "choices": ["Fastify", "Laravel"],
        },
    )

    response = client.get(
        f"/workflows/new-project/larv-skill/{session_id}/status",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run"]["state"] == "larv_full_waiting_for_input"
    assert payload["interactive_session"]["status"] == "waiting_for_input"
    assert payload["interactive_session"]["last_prompt"] == "Choose stack"
    assert payload["interactive_session"]["prompt_history"][-1]["prompt_id"] == "stack"
    assert payload["project_context_candidate"] is None
    assert "human.input_required" in [event["type"] for event in payload["events"]]


def test_larv_skill_status_reports_candidate_after_completion(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    project = tmp_path / "AeroTrack"
    project.mkdir()
    (project / "package.json").write_text('{"packageManager":"pnpm@9.0.0"}', encoding="utf-8")
    client = TestClient(create_app())
    headers = {"X-Hermes-Token": "secret-token"}
    started = client.post(
        "/workflows/new-project/larv-skill/session-started",
        headers=headers,
        json={
            "event_id": "event-start",
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(project),
        },
    ).json()
    session_id = started["interactive_session"]["id"]
    client.post(
        f"/workflows/new-project/larv-skill/{session_id}/completed",
        headers=headers,
        json={
            "event_id": "event-complete",
            "project_dir": str(project),
        },
    )

    response = client.get(
        f"/workflows/new-project/larv-skill/{session_id}/status",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run"]["state"] == "project_context_candidate_created"
    assert payload["interactive_session"]["status"] == "completed"
    assert payload["project_context_candidate"]["project_name"] == "AeroTrack"
    assert payload["project_context_candidate"]["blueprint"]["package_manager"] == "pnpm"


def test_larv_skill_status_returns_404_for_unknown_session(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    client = TestClient(create_app())

    response = client.get(
        "/workflows/new-project/larv-skill/sess_missing/status",
        headers={"X-Hermes-Token": "secret-token"},
    )

    assert response.status_code == 404
    assert "Interactive session not found" in response.json()["detail"]
