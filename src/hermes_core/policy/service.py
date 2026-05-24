from pydantic import BaseModel

from hermes_core.policy.rules import (
    AGENT_PATH_SCOPES,
    DENIED_ACTIONS,
    HIGH_RISK_TARGET_HINTS,
    ISSUE_PR_APPROVAL_STATES,
)


class PolicyRequest(BaseModel):
    agent_id: str
    workflow_type: str
    action: str
    target: str
    approval_state: str
    justification: str = ""


class PolicyResult(BaseModel):
    decision: str
    reason: str


class PolicyService:
    def evaluate(self, request: PolicyRequest) -> PolicyResult:
        denied = DENIED_ACTIONS.get(request.agent_id, set())
        if request.action in denied:
            return PolicyResult(decision="denied", reason="Action denied for agent role.")

        if (
            request.workflow_type == "issue_fix"
            and request.action == "github.create_pr"
            and request.approval_state not in ISSUE_PR_APPROVAL_STATES
        ):
            return PolicyResult(
                decision="needs_human_approval",
                reason="Issue-fix PR creation requires human approval checkpoint.",
            )

        target_lower = request.target.lower()
        if any(hint in target_lower for hint in HIGH_RISK_TARGET_HINTS):
            return PolicyResult(
                decision="needs_escalation",
                reason="Target matches high-risk path hint.",
            )

        if request.action == "repo.apply_patch":
            scopes = AGENT_PATH_SCOPES.get(request.agent_id)
            if scopes and not request.target.startswith(scopes):
                return PolicyResult(
                    decision="needs_escalation",
                    reason="Target outside agent path scope.",
                )

        return PolicyResult(decision="allowed", reason="Request allowed by current policy.")
