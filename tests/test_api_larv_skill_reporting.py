from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_api_records_external_larv_skill_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    project = tmp_path / "AeroTrack"
    project.mkdir()
    (project / "package.json").write_text('{"packageManager":"pnpm@9.0.0"}', encoding="utf-8")
    client = TestClient(create_app())

    started = client.post(
        "/workflows/new-project/larv-skill/session-started",
        json={
            "project_name": "AeroTrack",
            "external_session_id": "dtt-session-123",
            "cwd": str(project),
        },
    )
    assert started.status_code == 200
    session_id = started.json()["interactive_session"]["id"]

    output = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/output",
        json={"output": "Human chose Fastify and Next.js."},
    )
    assert output.status_code == 200

    answer = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/human-answer",
        json={"prompt_id": "stack", "answer": "Fastify and Next.js"},
    )
    assert answer.status_code == 200
    assert answer.json()["run"]["state"] == "larv_full_input_received"

    completed = client.post(
        f"/workflows/new-project/larv-skill/{session_id}/completed",
        json={"project_dir": str(project)},
    )
    assert completed.status_code == 200
    assert completed.json()["run"]["state"] == "project_context_candidate_created"
