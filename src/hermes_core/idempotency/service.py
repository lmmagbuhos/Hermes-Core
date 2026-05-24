from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from hermes_core.models import IdempotencyRecord


class IdempotencyService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def get(self, event_id: str) -> IdempotencyRecord | None:
        with self.session_factory() as db:
            return db.get(IdempotencyRecord, event_id)

    def record(
        self,
        *,
        event_id: str,
        endpoint: str,
        response_payload: dict[str, Any],
        run_id: int | None = None,
    ) -> IdempotencyRecord:
        with self.session_factory() as db:
            existing = db.get(IdempotencyRecord, event_id)
            if existing is not None:
                return existing
            record = IdempotencyRecord(
                event_id=event_id,
                endpoint=endpoint,
                response_payload=response_payload,
                run_id=run_id,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
