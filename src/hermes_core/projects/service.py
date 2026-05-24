from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from hermes_core.models import ProjectContextCandidate


class ProjectContextCandidateService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create(
        self,
        *,
        run_id: int,
        project_name: str,
        blueprint: dict[str, Any],
    ) -> ProjectContextCandidate:
        with self.session_factory() as db:
            candidate = ProjectContextCandidate(
                run_id=run_id,
                project_name=project_name,
                blueprint=blueprint,
                status="candidate",
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            return candidate
