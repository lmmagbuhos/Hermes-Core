from hermes_core.db import create_session_factory, init_db
from hermes_core.memory.service import MemoryService


def test_memory_service_creates_candidate_learning(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = MemoryService(session_factory)

    record = service.create_candidate(
        type="test_setup_fact",
        scope="project",
        summary="Project uses pnpm for frontend tests.",
        details="Observed in package manager files during run.",
        confidence=0.95,
        evidence_refs=["run:1"],
        created_by_agent="hermes-qa",
        source_run_id=1,
    )

    assert record.status == "candidate"
    assert record.confidence == 0.95
    assert record.evidence_refs == ["run:1"]


def test_memory_service_auto_promotes_narrow_fact_with_evidence(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = MemoryService(session_factory)
    record = service.create_candidate(
        type="project_fact",
        scope="project",
        summary="Project frontend uses pnpm.",
        details="packageManager field is pnpm@9.",
        confidence=0.96,
        evidence_refs=["file:package.json"],
        created_by_agent="hermes-frontend",
        source_run_id=1,
    )

    promoted = service.promote_if_allowed(record.id)

    assert promoted.status == "promoted"
    assert promoted.reviewed_by == "auto"


def test_memory_service_does_not_auto_promote_governance_change(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = MemoryService(session_factory)
    record = service.create_candidate(
        type="permission_change",
        scope="global",
        summary="Allow Hermes-Backend to edit auth without escalation.",
        details="This would weaken a high-risk approval rule.",
        confidence=0.99,
        evidence_refs=["run:2"],
        created_by_agent="hermes-manager",
        source_run_id=2,
    )

    promoted = service.promote_if_allowed(record.id)

    assert promoted.status == "candidate"
    assert promoted.reviewed_by is None


def test_memory_service_lists_promoted_records_by_scope(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'hermes.db'}"
    engine, session_factory = create_session_factory(db_url)
    init_db(engine)
    service = MemoryService(session_factory)
    record = service.create_candidate(
        type="project_fact",
        scope="project:aerotrack",
        summary="AeroTrack backend test command is pytest.",
        details="Observed during QA verification.",
        confidence=0.93,
        evidence_refs=["run:3"],
        created_by_agent="hermes-qa",
        source_run_id=3,
    )
    service.promote_if_allowed(record.id)

    records = service.list_promoted(scope="project:aerotrack")

    assert [item.summary for item in records] == ["AeroTrack backend test command is pytest."]
