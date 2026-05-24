from dataclasses import dataclass
from hashlib import sha1

from sqlalchemy.orm import Session, sessionmaker

from hermes_core.execution.contracts import PtyProcess
from hermes_core.execution.interactive import PtyInteractiveRunner
from hermes_core.models import InteractiveSessionRecord
from hermes_core.sessions.service import InteractiveSessionService


@dataclass(frozen=True)
class RuntimeReadResult:
    session_id: str
    output: str
    status: str
    prompt_id: str | None


@dataclass(frozen=True)
class RuntimeStatus:
    session_id: str
    status: str
    process_id: int | None


class InteractiveRuntime:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        runner: PtyInteractiveRunner | None = None,
    ):
        self.session_factory = session_factory
        self.sessions = InteractiveSessionService(session_factory)
        self.runner = runner or PtyInteractiveRunner()
        self._processes: dict[str, PtyProcess] = {}

    def start(
        self,
        *,
        run_id: int,
        command: list[str],
        cwd: str,
        transcript_ref: str,
    ) -> InteractiveSessionRecord:
        process = self.runner.start(command, cwd)
        session = self.sessions.create(
            run_id=run_id,
            command=command,
            cwd=cwd,
            transcript_ref=transcript_ref,
            process_id=process.pid,
        )
        self._processes[session.id] = process
        return session

    def read(self, session_id: str, *, timeout: float = 0.2) -> RuntimeReadResult:
        process = self._processes.get(session_id)
        if process is None:
            session = self.sessions.mark_recovery_required(session_id)
            return RuntimeReadResult(session.id, output="", status=session.status, prompt_id=None)

        output = self.runner.read_available(process, timeout=timeout)
        if output:
            self.sessions.append_transcript(session_id, output)

        exit_code = self.runner.poll(process)
        if exit_code is not None:
            session = self.sessions.mark_completed(session_id)
            self._processes.pop(session_id, None)
            return RuntimeReadResult(session.id, output=output, status=session.status, prompt_id=None)

        prompt_id = self._detect_prompt_id(output)
        if prompt_id:
            session = self.sessions.mark_waiting_for_input(
                session_id,
                prompt=output.strip(),
                prompt_id=prompt_id,
            )
            return RuntimeReadResult(
                session.id,
                output=output,
                status=session.status,
                prompt_id=prompt_id,
            )

        session = self.sessions.get(session_id)
        return RuntimeReadResult(session.id, output=output, status=session.status, prompt_id=None)

    def write_input(self, session_id: str, value: str, *, prompt_id: str) -> InteractiveSessionRecord:
        process = self._processes.get(session_id)
        if process is None:
            return self.sessions.mark_recovery_required(session_id)
        session = self.sessions.record_stdin(
            session_id,
            prompt_id=prompt_id,
            answer=value.rstrip("\n"),
        )
        self.runner.write_stdin(process, value)
        return session

    def status(self, session_id: str) -> RuntimeStatus:
        process = self._processes.get(session_id)
        if process is None:
            session = self.sessions.mark_recovery_required(session_id)
            return RuntimeStatus(
                session_id=session.id,
                status=session.status,
                process_id=session.process_id,
            )

        exit_code = self.runner.poll(process)
        if exit_code is not None:
            session = self.sessions.mark_completed(session_id)
            self._processes.pop(session_id, None)
            return RuntimeStatus(
                session_id=session.id,
                status=session.status,
                process_id=session.process_id,
            )

        session = self.sessions.get(session_id)
        return RuntimeStatus(session_id=session.id, status=session.status, process_id=session.process_id)

    def _detect_prompt_id(self, output: str) -> str | None:
        stripped = output.strip()
        if not stripped:
            return None
        if "?" not in stripped and not stripped.endswith(":"):
            return None
        digest = sha1(stripped.encode()).hexdigest()[:12]
        return f"prompt_{digest}"
