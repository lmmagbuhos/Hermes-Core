from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from hermes_core.models import Run
from hermes_core.runs.state import WORKFLOW_STATES


class RunService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create_run(self, workflow_type: str, payload: dict[str, Any] | None = None) -> Run:
        if workflow_type not in WORKFLOW_STATES:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

        with self.session_factory() as session:
            run = Run(
                workflow_type=workflow_type,
                state="received",
                payload=payload or {},
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            self._emit(
                session,
                run_id=run.id,
                type="workflow.created",
                payload={
                    "workflow_type": workflow_type,
                    "state": run.state,
                },
            )
            return run

    def transition(
        self,
        run_id: int,
        next_state: str,
        payload_update: dict[str, Any] | None = None,
    ) -> Run:
        with self.session_factory() as session:
            run = session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run not found: {run_id}")

            allowed_states = WORKFLOW_STATES[run.workflow_type]
            if next_state not in allowed_states:
                raise ValueError(f"Invalid state for {run.workflow_type}: {next_state}")

            previous_state = run.state
            run.state = next_state
            run.payload = {**(run.payload or {}), **(payload_update or {})}
            session.add(run)
            session.commit()
            session.refresh(run)
            self._emit(
                session,
                run_id=run.id,
                type="workflow.state_changed",
                payload={
                    "workflow_type": run.workflow_type,
                    "from_state": previous_state,
                    "to_state": next_state,
                },
            )
            return run

    def _emit(
        self,
        session: Session,
        *,
        run_id: int,
        type: str,
        payload: dict[str, Any],
    ) -> None:
        from hermes_core.models import Event

        event = Event(type=type, payload=payload, run_id=run_id)
        session.add(event)
        session.commit()
