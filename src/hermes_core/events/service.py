from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from hermes_core.models import Event


class EventService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def emit(self, type: str, payload: dict[str, Any], run_id: int | None = None) -> Event:
        with self.session_factory() as session:
            event = Event(type=type, payload=payload, run_id=run_id)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
