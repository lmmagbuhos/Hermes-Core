from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_api_can_read_interactive_output_and_submit_stdin(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    script = tmp_path / "ask.py"
    script.write_text(
        "answer = input('Project name? ')\nprint(f'created:{answer}')\n",
        encoding="utf-8",
    )
    client = TestClient(create_app())
    started = client.post(
        "/workflows/new-project/larv-full/start",
        json={
            "project_name": "AeroTrack",
            "command": ["python3", str(script)],
            "cwd": str(tmp_path),
            "start_process": True,
        },
    ).json()
    session_id = started["interactive_session"]["id"]

    output = client.get(f"/interactive-sessions/{session_id}/output?timeout=2").json()
    assert "Project name?" in output["output"]
    assert output["status"] == "waiting_for_input"

    response = client.post(
        f"/interactive-sessions/{session_id}/stdin",
        json={
            "prompt_id": output["prompt_id"],
            "answer": "AeroTrack\n",
        },
    )
    assert response.status_code == 200

    output = client.get(f"/interactive-sessions/{session_id}/output?timeout=5").json()
    assert "created:AeroTrack" in output["output"]
    assert output["status"] == "completed"
