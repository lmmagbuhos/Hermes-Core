from collections.abc import Callable
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
