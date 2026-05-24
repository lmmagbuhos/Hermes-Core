from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Float, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int | None] = mapped_column(nullable=True)
    type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    scope: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="candidate")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_run_id: Mapped[int | None] = mapped_column(nullable=True)
    created_by_agent: Mapped[str] = mapped_column(String(120), nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )


class InteractiveSessionRecord(Base):
    __tablename__ = "interactive_sessions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    command: Mapped[list[str]] = mapped_column(JSON, default=list)
    cwd: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    transcript_ref: Mapped[str] = mapped_column(String(1000), nullable=False)
    process_id: Mapped[int | None] = mapped_column(nullable=True)
    last_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_history: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    stdin_history: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )


class ProjectContextCandidate(Base):
    __tablename__ = "project_context_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    blueprint: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    event_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    run_id: Mapped[int | None] = mapped_column(nullable=True)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
