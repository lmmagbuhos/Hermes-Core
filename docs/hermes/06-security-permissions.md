# Security and Permissions

Hermes security should be capability-based. It should prevent dangerous autonomy without blocking legitimate fixes and project creation.

## Policy Inputs

Every action is evaluated using:

```text
agent role
workflow type
project/repo scope
file path scope
command risk
data risk
approval state
environment
```

## Risk Tiers

### Low Risk

Allowed for relevant agents inside assigned scope:

```text
read files
search code
inspect git status/diff
read generated docs
create run notes
run non-destructive tests
apply patch to assigned files
summarize logs
```

### Medium Risk

Allowed only to specific roles or after ProjectManager authorization:

```text
install dependencies
change config files
modify CI files
start sandbox servers
run migrations in sandbox
modify package files
create new files
change tests
```

### High Risk

Requires escalation, Manager approval, or explicit workflow checkpoint:

```text
modify auth/security/payment code
edit env/secrets
delete files
destructive database commands
production commands
force push
merge PR
change agent permissions
change confidence thresholds
promote governance memory
```

High-risk actions are not permanently forbidden. They require justification and approval.

## Capability Request

Example:

```text
agent: Hermes-Backend
workflow: issue_fix
run_id: run_123
action: repo.apply_patch
target: backend/app/Http/Controllers/AuthController.php
risk: high
justification: Fixes acceptance criteria around login validation.
approval_state: project_manager_assigned
```

Policy response:

```text
allowed
denied
needs_escalation
needs_human_approval
needs_manager_approval
```

## Non-Negotiable Guards

```text
No agent may expand its own permissions through learning.
No memory record may weaken approval rules without governance approval.
No workflow may skip required human checkpoints.
No issue-fix workflow may PR/push without human checkpoint in the first version.
```

## Required Issue-Fix Checkpoint

Before PR/push:

```text
Hermes must provide final report + sandbox URL.
Human confirms before PR creation or push.
```

