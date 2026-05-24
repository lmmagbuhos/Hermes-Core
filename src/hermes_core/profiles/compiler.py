from typing import Any

from hermes_core.profiles.loader import AgentProfile


def compile_runtime_context(
    *,
    profile: AgentProfile,
    workflow_state: str,
    task_context: dict[str, Any],
    memory: list[str],
    tools: list[str],
) -> str:
    responsibilities = "\n".join(f"- {item}" for item in profile.responsibilities)
    non_responsibilities = "\n".join(f"- {item}" for item in profile.non_responsibilities)
    memory_lines = "\n".join(f"- {item}" for item in memory) or "- No promoted memory loaded."
    tool_lines = "\n".join(f"- {item}" for item in tools)
    task_lines = "\n".join(f"- {key}: {value}" for key, value in task_context.items())
    path_scope_lines = "\n".join(f"- {item}" for item in profile.path_scopes) or "- No path scope."

    return f"""# Agent
Name: {profile.name}
Role: {profile.role_contract}
Workflow state: {workflow_state}

# Responsibilities
{responsibilities}

# Non-Responsibilities
{non_responsibilities}

# Path Scope
{path_scope_lines}

# Task Context
{task_lines}

# Relevant Memory
{memory_lines}

# Available Tools
{tool_lines}

# Operating Rule
Use only the listed tools. Respect non-responsibilities and escalate when the
task requires denied tools, out-of-scope paths, or high-risk actions.
"""

