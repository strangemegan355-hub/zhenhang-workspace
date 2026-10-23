from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class TaskQueue(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "task_queue"

    queue_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_retry: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    dead_letter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    creator: Mapped[User | None] = relationship(foreign_keys="TaskQueue.created_by", lazy="joined")


class JobExecution(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "job_executions"

    job_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual", server_default="manual")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running", server_default="running", index=True)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    creator: Mapped[User | None] = relationship(foreign_keys="JobExecution.created_by", lazy="joined")
