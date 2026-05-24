import subprocess
from pathlib import Path

from hermes_core.execution.contracts import CommandResult


class LocalExecutionAdapter:
    def run_command(self, command: list[str], cwd: str) -> CommandResult:
        result = subprocess.run(
            command,
            cwd=Path(cwd),
            check=False,
            capture_output=True,
            text=True,
        )
        return CommandResult(
            command=command,
            cwd=cwd,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
