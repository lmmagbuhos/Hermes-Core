HIGH_RISK_TARGET_HINTS = (
    ".env",
    "secret",
    "auth",
    "payment",
    "billing",
)

AGENT_PATH_SCOPES = {
    "hermes-frontend": ("frontend/", "web/", "resources/js/", "src/"),
    "hermes-backend": ("backend/", "app/", "server/", "api/"),
    "hermes-database": ("database/", "backend/database/", "migrations/", "seeders/", "schema/"),
}

DENIED_ACTIONS = {
    "hermes-qa": {"repo.apply_patch"},
    "hermes-triage": {"repo.apply_patch", "terminal.run_command"},
    "hermes-manager": {"repo.apply_patch"},
}

ISSUE_PR_APPROVAL_STATES = {
    "human_pr_approved",
}

