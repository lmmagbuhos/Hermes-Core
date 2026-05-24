from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from hermes_core.models import InteractiveSessionRecord


class InteractiveSessionService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create(
        self,
        *,
        run_id: int,
        command: list[str],
        cwd: str,
        transcript_ref: str,
        process_id: int | None = None,
    ) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = InteractiveSessionRecord(
                id=f"sess_{uuid4().hex}",
                run_id=run_id,
                command=command,
                cwd=cwd,
                status="running",
                transcript_ref=transcript_ref,
                process_id=process_id,
                prompt_history=[],
                stdin_history=[],
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def get(self, session_id: str) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            return record

    def mark_waiting_for_input(
        self,
        session_id: str,
        *,
        prompt: str,
        prompt_id: str,
        choices: list[str] | None = None,
        default: str | None = None,
        is_required: bool = True,
        metadata: dict[str, object] | None = None,
    ) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            record.status = "waiting_for_input"
            record.last_prompt = prompt
            record.prompt_history = [
                *(record.prompt_history or []),
                {
                    "prompt_id": prompt_id,
                    "prompt": prompt,
                    "choices": choices or [],
                    "default": default,
                    "is_required": is_required,
                    "metadata": metadata or {},
                },
            ]
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def record_stdin(
        self,
        session_id: str,
        *,
        prompt_id: str,
        answer: str,
    ) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            history = record.stdin_history or []
            if any(item["prompt_id"] == prompt_id for item in history):
                raise ValueError(f"Prompt {prompt_id} already received stdin")
            record.status = "resumed"
            record.stdin_history = [
                *history,
                {
                    "prompt_id": prompt_id,
                    "answer": answer,
                },
            ]
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def set_process_id(self, session_id: str, *, process_id: int) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            record.process_id = process_id
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def append_transcript(self, session_id: str, chunk: str) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            transcript_path = Path(record.transcript_ref)
            transcript_path.parent.mkdir(parents=True, exist_ok=True)
            with transcript_path.open("a", encoding="utf-8") as handle:
                handle.write(chunk)
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def mark_completed(self, session_id: str) -> InteractiveSessionRecord:
        return self._set_status(session_id, "completed")

    def mark_recovery_required(self, session_id: str) -> InteractiveSessionRecord:
        return self._set_status(session_id, "recovery_required")

    def _set_status(self, session_id: str, status: str) -> InteractiveSessionRecord:
        with self.session_factory() as db:
            record = db.get(InteractiveSessionRecord, session_id)
            if record is None:
                raise ValueError(f"Interactive session not found: {session_id}")
            record.status = status
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
