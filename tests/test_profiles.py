from hermes_core.profiles.compiler import compile_runtime_context
from hermes_core.profiles.loader import load_profile, load_profiles


def test_loads_triage_profile():
    profile = load_profile("profiles/hermes-triage.yaml")

    assert profile.id == "hermes-triage"
    assert profile.name == "Hermes-Triage"
    assert profile.type == "triage"
    assert "ticket.normalize" in profile.allowed_tools
    assert "repo.apply_patch" in profile.denied_tools
    assert profile.model_provider == "minimax"


def test_loads_all_required_profiles():
    profiles = load_profiles("profiles")
    ids = {profile.id for profile in profiles}

    assert {
        "hermes-triage",
        "hermes-manager",
        "hermes-project-manager",
        "hermes-frontend",
        "hermes-backend",
        "hermes-database",
        "hermes-qa",
    }.issubset(ids)


def test_profiles_keep_tactical_workers_separate():
    profiles = {profile.id: profile for profile in load_profiles("profiles")}

    assert "database/migrations/" in profiles["hermes-database"].path_scopes
    assert "frontend/" in profiles["hermes-frontend"].path_scopes
    assert "backend/" in profiles["hermes-backend"].path_scopes
    assert "repo.apply_patch" in profiles["hermes-qa"].denied_tools
    assert "repo.apply_patch" not in profiles["hermes-qa"].allowed_tools


def test_compiles_runtime_context_from_profile_and_run_data():
    profile = load_profile("profiles/hermes-backend.yaml")

    context = compile_runtime_context(
        profile=profile,
        workflow_state="implementation_running",
        task_context={
            "ticket": "Fix login validation",
            "allowed_paths": ["backend/app/"],
        },
        memory=[
            "Backend validation errors use ProblemDetails format.",
        ],
        tools=["repo.read_file", "repo.search", "repo.apply_patch"],
    )

    assert "Hermes-Backend" in context
    assert "Fix login validation" in context
    assert "ProblemDetails" in context
    assert "repo.apply_patch" in context
    assert "Use only the listed tools" in context
