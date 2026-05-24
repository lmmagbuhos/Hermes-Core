from fastapi.testclient import TestClient

from hermes_core.app import create_app


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_profiles_endpoint_lists_profiles():
    client = TestClient(create_app())

    response = client.get("/profiles")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["profiles"]}
    assert "Hermes-Triage" in names
    assert "Hermes-Backend" in names


def test_create_run_endpoint_creates_issue_fix_run(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    monkeypatch.setenv("HERMES_DATABASE_URL", db_url)

    client = TestClient(create_app())
    response = client.post(
        "/runs",
        json={
            "workflow_type": "issue_fix",
            "payload": {"ticket": "BUG-123"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["workflow_type"] == "issue_fix"
    assert body["state"] == "received"
    assert body["payload"]["ticket"] == "BUG-123"
