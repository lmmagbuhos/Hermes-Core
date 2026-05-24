from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from hermes_core.models import MemoryRecord

AUTO_PROMOTABLE_TYPES = {
    "project_fact",
    "test_setup_fact",
    "frontend_fact",
    "backend_fact",
    "database_fact",
}

GOVERNANCE_GATED_TYPES = {
    "permission_change",
    "security_policy_change",
    "confidence_threshold_change",
    "approval_gate_change",
}

AUTO_PROMOTION_MIN_CONFIDENCE = 0.9


class MemoryService:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def create_candidate(
        self,
        *,
        type: str,
        scope: str,
        summary: str,
        details: str,
        confidence: float,
        evidence_refs: list[str],
        created_by_agent: str,
        source_run_id: int | None = None,
    ) -> MemoryRecord:
        with self.session_factory() as session:
            record = MemoryRecord(
                type=type,
                scope=scope,
                summary=summary,
                details=details,
                status="candidate",
                confidence=confidence,
                evidence_refs=evidence_refs,
                source_run_id=source_run_id,
                created_by_agent=created_by_agent,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def promote_if_allowed(self, record_id: int) -> MemoryRecord:
        with self.session_factory() as session:
            record = session.get(MemoryRecord, record_id)
            if record is None:
                raise ValueError(f"Memory record not found: {record_id}")

            if self._can_auto_promote(record):
                record.status = "promoted"
                record.reviewed_by = "auto"
                session.add(record)
                session.commit()
                session.refresh(record)

            return record

    def list_promoted(self, *, scope: str) -> list[MemoryRecord]:
        with self.session_factory() as session:
            statement = (
                select(MemoryRecord)
                .where(MemoryRecord.scope == scope)
                .where(MemoryRecord.status == "promoted")
                .order_by(MemoryRecord.id)
            )
            return list(session.scalars(statement).all())

    def _can_auto_promote(self, record: MemoryRecord) -> bool:
        if record.type in GOVERNANCE_GATED_TYPES:
            return False
        return (
            record.type in AUTO_PROMOTABLE_TYPES
            and record.confidence >= AUTO_PROMOTION_MIN_CONFIDENCE
            and len(record.evidence_refs) > 0
        )
