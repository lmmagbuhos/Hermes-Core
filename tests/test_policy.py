from hermes_core.policy.service import PolicyRequest, PolicyService


def test_frontend_can_patch_frontend_path():
    service = PolicyService()

    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-frontend",
            workflow_type="issue_fix",
            action="repo.apply_patch",
            target="frontend/src/App.tsx",
            approval_state="project_manager_assigned",
        )
    )

    assert result.decision == "allowed"
    assert "allowed" in result.reason.lower()


def test_frontend_database_patch_requires_escalation():
    service = PolicyService()

    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-frontend",
            workflow_type="issue_fix",
            action="repo.apply_patch",
            target="backend/database/migrations/2026_01_01_create_users.php",
            approval_state="project_manager_assigned",
        )
    )

    assert result.decision == "needs_escalation"
    assert "outside agent path scope" in result.reason


def test_qa_cannot_patch_source():
    service = PolicyService()

    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-qa",
            workflow_type="issue_fix",
            action="repo.apply_patch",
            target="backend/app/Service.php",
            approval_state="qa_verification",
        )
    )

    assert result.decision == "denied"


def test_auth_change_requires_escalation_even_for_backend():
    service = PolicyService()

    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-backend",
            workflow_type="issue_fix",
            action="repo.apply_patch",
            target="backend/app/Auth/LoginController.py",
            approval_state="project_manager_assigned",
            justification="Fix login validation acceptance criteria.",
        )
    )

    assert result.decision == "needs_escalation"
    assert "high-risk" in result.reason


def test_human_checkpoint_required_for_issue_pr_creation():
    service = PolicyService()

    result = service.evaluate(
        PolicyRequest(
            agent_id="hermes-manager",
            workflow_type="issue_fix",
            action="github.create_pr",
            target="repo:example/project",
            approval_state="manager_audit_done",
        )
    )

    assert result.decision == "needs_human_approval"
