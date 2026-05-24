# Issue Fix Workflow

For issue fixing, Hermes uses confidence debate to decide whether Hermes-{projectName} can fix alone or whether the full assembly line is required.

## Workflow

```text
1. Ticket received
2. Hermes-Triage normalization
3. Project agent lookup
4. MAD confidence debate
5. Execution topology decision
6. Implementation
7. Hermes-QA verification
8. Hermes-{projectName} diff review
9. Hermes-Manager audit
10. Human checkpoint before PR/push
11. Learning candidates created
12. Workflow completed
```

## Triage

Hermes-Triage extracts:

```text
repository/project
issue summary
reproduction details
expected behavior
actual behavior
acceptance criteria
ambiguity flags
required human clarifications
```

If the ticket is too ambiguous, Triage rejects or asks for clarification.

## Project Agent Lookup

Hermes locates the permanent `Hermes-{projectName}` profile.

If no project agent exists, the ticket cannot use normal maintenance mode. It should go through a future onboarding/adoption workflow.

## MAD Confidence Debate

Hermes-ProjectManager and Hermes-{projectName} independently score the task.

Scoring considers:

```text
file scope clarity
reproduction clarity
expected blast radius
dependency risk
database risk
auth/security/payment risk
test availability
prior project memory
ambiguity level
```

Final confidence:

```text
C_Final = min(C_PM, C_Project)
```

## Execution Topology

```text
If C_Final >= 90:
  Solo Maintainer Mode

If C_Final < 90:
  Assembly Line Mode
```

## Solo Maintainer Mode

Hermes-{projectName}:

```text
reads relevant files
creates patch plan
applies scoped code changes
runs appropriate tests
reviews its own diff against project memory
creates final report
```

Solo mode means solo implementation, not unsupervised release. The first version still requires a final report and sandbox URL before PR/push.

## Assembly Line Mode

Hermes-{projectName} becomes Context Oracle and produces:

```text
blast radius analysis
files likely involved
files forbidden or risky
project conventions
historical pitfalls
recommended tests
veto conditions
```

Hermes-ProjectManager creates a sequential worker plan using:

```text
Hermes-Frontend
Hermes-Backend
Hermes-Database
Hermes-QA
```

Hermes-QA verifies acceptance criteria through tests, lint, builds, sandbox checks, and reproduction checks where possible.

Hermes-{projectName} performs final diff review and may veto changes that violate project memory, architecture, or blast-radius constraints.

Hermes-Manager performs final policy and security audit.

## Human Checkpoint

Before PR/push, Hermes must submit:

```text
final report
files changed
tests run
sandbox URL
risks
recommendation
```

The human must confirm before PR creation or push.

