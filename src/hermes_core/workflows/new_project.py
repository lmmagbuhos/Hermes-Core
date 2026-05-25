from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from hermes_core.artifacts.errors import ArtifactValidationError
from hermes_core.artifacts.ingest import ingest_project_artifacts
from hermes_core.events.service import EventService
from hermes_core.models import Event, InteractiveSessionRecord, ProjectContextCandidate, Run
from hermes_core.projects.service import ProjectContextCandidateService
from hermes_core.runtime.interactive import InteractiveRuntime, RuntimeReadResult
from hermes_core.runs.service import RunService
from hermes_core.sessions.service import InteractiveSessionService


@dataclass(frozen=True)
class NewProjectWorkflowResult:
    run: Run
    interactive_session: InteractiveSessionRecord


@dataclass(frozen=True)
class LarvSkillSessionStatus:
    run: Run
    interactive_session: InteractiveSessionRecord
    events: list[Event]
    project_context_candidate: ProjectContextCandidate | None


class NewProjectWorkflowService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory
        self.runs = RunService(session_factory)
        self.sessions = InteractiveSessionService(session_factory)
        self.events = EventService(session_factory)
        self.candidates = ProjectContextCandidateService(session_factory)
        self.runtime = InteractiveRuntime(session_factory)

    def start_larv_full(
        self,
        *,
        project_name: str,
        command: list[str],
        cwd: str,
        start_process: bool = False,
    ) -> NewProjectWorkflowResult:
        run = self.runs.create_run(
            "new_project_creation",
            {
                "project_name": project_name,
                "cwd": cwd,
            },
        )
        transcript_ref = str(Path(cwd) / ".hermes" / "transcripts" / f"run_{run.id}.log")
        if start_process:
            interactive_session = self.runtime.start(
                run_id=run.id,
                command=command,
                cwd=cwd,
                transcript_ref=transcript_ref,
            )
        else:
            interactive_session = self.sessions.create(
                run_id=run.id,
                command=command,
                cwd=cwd,
                transcript_ref=transcript_ref,
            )
        run = self.runs.transition(
            run.id,
            "larv_full_session_started",
            {"interactive_session_id": interactive_session.id},
        )
        self.events.emit(
            "terminal.session_started",
            {"session_id": interactive_session.id, "command": command},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def waiting_for_input(
        self,
        session_id: str,
        *,
        prompt_id: str,
        prompt: str,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.mark_waiting_for_input(
            session_id,
            prompt=prompt,
            prompt_id=prompt_id,
        )
        run = self.runs.transition(
            interactive_session.run_id,
            "larv_full_waiting_for_input",
            {"last_prompt": prompt, "last_prompt_id": prompt_id},
        )
        self.events.emit(
            "human.input_required",
            {"session_id": session_id, "prompt_id": prompt_id, "prompt": prompt},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def submit_human_input(
        self,
        session_id: str,
        *,
        prompt_id: str,
        answer: str,
    ) -> NewProjectWorkflowResult:
        if session_id in self.runtime._processes:
            interactive_session = self.runtime.write_input(session_id, answer, prompt_id=prompt_id)
        else:
            interactive_session = self.sessions.record_stdin(
                session_id,
                prompt_id=prompt_id,
                answer=answer,
            )
        run = self.runs.transition(
            interactive_session.run_id,
            "larv_full_input_received",
            {"last_answer_prompt_id": prompt_id},
        )
        self.events.emit(
            "human.input_received",
            {"session_id": session_id, "prompt_id": prompt_id},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def read_interactive_output(
        self,
        session_id: str,
        *,
        timeout: float = 0.2,
    ) -> RuntimeReadResult:
        return self.runtime.read(session_id, timeout=timeout)

    def complete_larv_full(
        self,
        session_id: str,
        *,
        transcript: str,
        project_dir: Path,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.get(session_id)
        run = self.runs.transition(interactive_session.run_id, "larv_full_completed")
        blueprint = ingest_project_artifacts(project_dir=project_dir, transcript=transcript)
        run = self.runs.transition(
            run.id,
            "larv_artifacts_ingested",
            {"blueprint": blueprint.model_dump()},
        )
        candidate = self.candidates.create(
            run_id=run.id,
            project_name=blueprint.project_name,
            blueprint=blueprint.model_dump(),
        )
        run = self.runs.transition(
            run.id,
            "project_context_candidate_created",
            {"project_context_candidate_id": candidate.id},
        )
        self.events.emit(
            "artifact.blueprint_created",
            {"project_name": blueprint.project_name, "candidate_id": candidate.id},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def record_larv_skill_session_started(
        self,
        *,
        project_name: str,
        external_session_id: str,
        cwd: str,
    ) -> NewProjectWorkflowResult:
        run = self.runs.create_run(
            "new_project_creation",
            {
                "project_name": project_name,
                "cwd": cwd,
                "external_larv_session_id": external_session_id,
                "invocation_owner": "dtt_ai_agent_runtime",
            },
        )
        transcript_ref = str(Path(cwd) / ".hermes" / "transcripts" / f"run_{run.id}.log")
        interactive_session = self.sessions.create(
            run_id=run.id,
            command=["skill:larv:full"],
            cwd=cwd,
            transcript_ref=transcript_ref,
        )
        run = self.runs.transition(
            run.id,
            "larv_full_session_started",
            {"interactive_session_id": interactive_session.id},
        )
        self.events.emit(
            "larv.skill_session_started",
            {
                "session_id": interactive_session.id,
                "external_session_id": external_session_id,
                "project_name": project_name,
            },
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def record_larv_skill_output(
        self,
        session_id: str,
        *,
        output: str,
        stream: str = "agent",
        sequence: int | None = None,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.append_transcript(session_id, output)
        run = self._get_run(interactive_session.run_id)
        self.events.emit(
            "terminal.stdout",
            {
                "session_id": session_id,
                "bytes": len(output),
                "stream": stream,
                "sequence": sequence,
            },
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def record_larv_skill_prompt_shown(
        self,
        session_id: str,
        *,
        prompt_id: str,
        prompt: str,
        choices: list[str] | None = None,
        default: str | None = None,
        is_required: bool = True,
        metadata: dict[str, object] | None = None,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.mark_waiting_for_input(
            session_id,
            prompt=prompt,
            prompt_id=prompt_id,
            choices=choices,
            default=default,
            is_required=is_required,
            metadata=metadata,
        )
        run = self.runs.transition(
            interactive_session.run_id,
            "larv_full_waiting_for_input",
            {"last_prompt": prompt, "last_prompt_id": prompt_id},
        )
        self.events.emit(
            "human.input_required",
            {
                "session_id": session_id,
                "prompt_id": prompt_id,
                "prompt": prompt,
                "choices": choices or [],
                "default": default,
                "is_required": is_required,
                "metadata": metadata or {},
            },
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def record_larv_skill_human_answer(
        self,
        session_id: str,
        *,
        prompt_id: str,
        answer: str,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.record_stdin(
            session_id,
            prompt_id=prompt_id,
            answer=answer,
        )
        run = self.runs.transition(
            interactive_session.run_id,
            "larv_full_input_received",
            {"last_answer_prompt_id": prompt_id},
        )
        self.events.emit(
            "human.input_received",
            {"session_id": session_id, "prompt_id": prompt_id},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def complete_external_larv_skill_session(
        self,
        session_id: str,
        *,
        project_dir: Path,
    ) -> NewProjectWorkflowResult:
        self._validate_project_dir(project_dir)
        interactive_session = self.sessions.get(session_id)
        transcript_path = Path(interactive_session.transcript_ref)
        transcript = self._read_optional_transcript(transcript_path)
        run = self.runs.transition(interactive_session.run_id, "larv_full_completed")
        try:
            blueprint = ingest_project_artifacts(project_dir=project_dir, transcript=transcript)
        except ArtifactValidationError:
            raise
        except Exception as error:
            raise ArtifactValidationError(
                code="artifact_ingestion_failed",
                message=f"Unable to ingest generated project artifacts: {error}",
                path=str(project_dir),
            ) from error
        run = self.runs.transition(
            run.id,
            "larv_artifacts_ingested",
            {"blueprint": blueprint.model_dump()},
        )
        candidate = self.candidates.create(
            run_id=run.id,
            project_name=blueprint.project_name,
            blueprint=blueprint.model_dump(),
        )
        run = self.runs.transition(
            run.id,
            "project_context_candidate_created",
            {"project_context_candidate_id": candidate.id},
        )
        self.events.emit(
            "larv.skill_session_completed",
            {"session_id": session_id, "candidate_id": candidate.id},
            run_id=run.id,
        )
        interactive_session = self.sessions.mark_completed(session_id)
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def record_larv_skill_failed(
        self,
        session_id: str,
        *,
        reason: str,
    ) -> NewProjectWorkflowResult:
        interactive_session = self.sessions.mark_recovery_required(session_id)
        run = self.runs.transition(
            interactive_session.run_id,
            "failed",
            {"failure_reason": reason},
        )
        self.events.emit(
            "larv.skill_session_failed",
            {"session_id": session_id, "reason": reason},
            run_id=run.id,
        )
        return NewProjectWorkflowResult(run=run, interactive_session=interactive_session)

    def get_larv_skill_session_status(
        self,
        session_id: str,
        *,
        event_limit: int = 10,
    ) -> LarvSkillSessionStatus:
        with self.session_factory() as db:
            interactive_session = db.get(InteractiveSessionRecord, session_id)
            if interactive_session is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            run = db.get(Run, interactive_session.run_id)
            if run is None:
                raise ValueError(f"Run not found: {interactive_session.run_id}")
            events = (
                db.query(Event)
                .filter(Event.run_id == run.id)
                .order_by(Event.id.desc())
                .limit(event_limit)
                .all()
            )
            candidate = (
                db.query(ProjectContextCandidate)
                .filter(ProjectContextCandidate.run_id == run.id)
                .order_by(ProjectContextCandidate.id.desc())
                .first()
            )
            db.expunge(interactive_session)
            db.expunge(run)
            for event in events:
                db.expunge(event)
            if candidate is not None:
                db.expunge(candidate)
            return LarvSkillSessionStatus(
                run=run,
                interactive_session=interactive_session,
                events=list(reversed(events)),
                project_context_candidate=candidate,
            )

    def _get_run(self, run_id: int) -> Run:
        with self.session_factory() as db:
            run = db.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run not found: {run_id}")
            return run

    def _validate_project_dir(self, project_dir: Path) -> None:
        if not project_dir.exists():
            raise ArtifactValidationError(
                code="project_dir_missing",
                message=f"Project directory does not exist: {project_dir}",
                path=str(project_dir),
            )
        if not project_dir.is_dir():
            raise ArtifactValidationError(
                code="project_dir_not_directory",
                message=f"Project path is not a directory: {project_dir}",
                path=str(project_dir),
            )
        try:
            next(project_dir.iterdir(), None)
        except OSError as error:
            raise ArtifactValidationError(
                code="project_dir_not_readable",
                message=f"Project directory is not readable by Hermes Core: {error}",
                path=str(project_dir),
            ) from error

    def _read_optional_transcript(self, transcript_path: Path) -> str:
        if not transcript_path.exists():
            return ""
        try:
            return transcript_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ArtifactValidationError(
                code="transcript_not_readable",
                message=f"Transcript file is not readable by Hermes Core: {error}",
                path=str(transcript_path),
            ) from error


def larv_skill_session_status_payload(status: LarvSkillSessionStatus) -> dict[str, Any]:
    return {
        "run": {
            "id": status.run.id,
            "workflow_type": status.run.workflow_type,
            "state": status.run.state,
            "payload": status.run.payload,
        },
        "interactive_session": {
            "id": status.interactive_session.id,
            "run_id": status.interactive_session.run_id,
            "command": status.interactive_session.command,
            "cwd": status.interactive_session.cwd,
            "status": status.interactive_session.status,
            "last_prompt": status.interactive_session.last_prompt,
            "transcript_ref": status.interactive_session.transcript_ref,
            "prompt_history": status.interactive_session.prompt_history or [],
            "stdin_history": status.interactive_session.stdin_history or [],
        },
        "events": [
            {
                "id": event.id,
                "type": event.type,
                "payload": event.payload,
                "created_at": event.created_at.isoformat(),
            }
            for event in status.events
        ],
        "project_context_candidate": (
            {
                "id": status.project_context_candidate.id,
                "project_name": status.project_context_candidate.project_name,
                "status": status.project_context_candidate.status,
                "blueprint": status.project_context_candidate.blueprint,
            }
            if status.project_context_candidate is not None
            else None
        ),
    }
