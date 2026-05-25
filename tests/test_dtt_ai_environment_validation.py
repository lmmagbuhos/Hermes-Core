import importlib.util
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from hermes_core.app import create_app
from hermes_core.integrations.dtt_ai.validation import validate_dtt_ai_environment


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "tools" / "validate_dtt_ai_environment.py"
SPEC = importlib.util.spec_from_file_location("validate_dtt_ai_environment_script", SCRIPT_PATH)
assert SPEC is not None
validation_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validation_script)


def test_validation_fails_when_workspace_path_is_missing(tmp_path):
    missing = tmp_path / "missing"

    report = validate_dtt_ai_environment(
        hermes_url="http://unused",
        workspace_path=str(missing),
    )

    assert report.ok is False
    assert report.checks[0].name == "workspace_path"
    assert "does not exist" in report.checks[0].detail


def test_validation_passes_against_hermes_app(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_DATABASE_URL", f"sqlite:///{tmp_path / 'hermes.db'}")
    monkeypatch.setenv("HERMES_DTT_AI_SHARED_TOKEN", "secret-token")
    workspace = tmp_path / "dtt-ai-workspace"
    workspace.mkdir()
    app_client = TestClient(create_app())

    def handler(request: httpx.Request) -> httpx.Response:
        response = app_client.request(
            request.method,
            request.url.path,
            headers=dict(request.headers),
            content=request.content,
        )
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client

    def mocked_get(url: str, **kwargs):
        with original_client(transport=transport, base_url="http://testserver") as client:
            return client.get(url, **kwargs)

    def mocked_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "get", mocked_get)
    monkeypatch.setattr(httpx, "Client", mocked_client)

    report = validate_dtt_ai_environment(
        hermes_url="http://testserver",
        token="secret-token",
        workspace_path=str(workspace),
        project_name="ValidationProject",
    )

    assert report.ok is True
    assert [check.name for check in report.checks] == [
        "workspace_path",
        "hermes_health",
        "completion_flow",
        "failure_flow",
    ]
    assert all(check.ok for check in report.checks)


def test_validation_cli_requires_workspace_path(monkeypatch, capsys):
    monkeypatch.delenv("DTT_AI_WORKSPACE_PATH", raising=False)
    monkeypatch.setattr(
        validation_script.sys,
        "argv",
        ["validate_dtt_ai_environment.py", "--hermes-url", "http://testserver"],
    )

    try:
        validation_script.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("Expected missing workspace path to exit with failure")

    output = capsys.readouterr().out
    assert "Provide --workspace-path" in output
