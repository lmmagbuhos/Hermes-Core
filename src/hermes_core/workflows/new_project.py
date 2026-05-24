from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from hermes_core.artifacts.ingest import ingest_project_artifacts
from hermes_core.events.service import EventService
from hermes_core.models import InteractiveSessionRecord, Run
from hermes_core.projects.service import ProjectContextCandidateService
from hermes_core.runtime.interactive import InteractiveRuntime, RuntimeReadResult
from hermes_core.runs.service import RunService
from hermes_core.sessions.service import InteractiveSessionService


@dataclass(frozen=True)
class NewProjectWorkflowResult:
    run: Run
    interactive_session: InteractiveSessionRecord


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
        if not project_dir.exists():
            raise ValueError(f"project_dir does not exist: {project_dir}")
        interactive_session = self.sessions.mark_completed(session_id)
        transcript_path = Path(interactive_session.transcript_ref)
        transcript = (
            transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else ""
        )
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
            "larv.skill_session_completed",
            {"session_id": session_id, "candidate_id": candidate.id},
            run_id=run.id,
        )
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

    def _get_run(self, run_id: int) -> Run:
        with self.session_factory() as db:
            run = db.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run not found: {run_id}")
            return run
