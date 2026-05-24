from hermes_core.artifacts.ingest import ingest_project_artifacts
from hermes_core.db import create_session_factory, init_db
from hermes_core.projects.service import ProjectContextCandidateService


def test_ingests_generated_project_artifacts(tmp_path):
    project = tmp_path / "AeroTrack"
    project.mkdir()
    (project / "package.json").write_text('{"packageManager":"pnpm@9.0.0"}', encoding="utf-8")
    docs = project / "docs" / "Handsoff"
    docs.mkdir(parents=True)
    (docs / "slice-01-backend.md").write_text("# Backend Slice\nBuild API", encoding="utf-8")

    blueprint = ingest_project_artifacts(
        project_dir=project,
        transcript="Human chose Fastify and Next.js.",
    )

    assert blueprint.project_name == "AeroTrack"
    assert blueprint.package_manager == "pnpm"
    assert blueprint.transcript_summary == "Human chose Fastify and Next.js."
    assert blueprint.implementation_slices == ["docs/Handsoff/slice-01-backend.md"]


def test_creates_project_context_candidate(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = ProjectContextCandidateService(session_factory)

    candidate = service.create(
        run_id=9,
        project_name="AeroTrack",
        blueprint={
            "project_name": "AeroTrack",
            "package_manager": "pnpm",
            "implementation_slices": ["docs/Handsoff/slice-01-backend.md"],
        },
    )

    assert candidate.id is not None
    assert candidate.status == "candidate"
    assert candidate.blueprint["package_manager"] == "pnpm"
