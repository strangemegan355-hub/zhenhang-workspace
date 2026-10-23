from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.machine import Machine
    from app.models.project import Project
    from app.models.user import User


class WorkOrder(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "work_orders"

    work_order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    machine_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("machines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_desc: Mapped[str] = mapped_column(String(255), nullable=False)
    process_node: Mapped[str] = mapped_column(String(32), nullable=False, default="assembly", server_default="assembly", index=True)
    team: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    claimed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="todo", server_default="todo", index=True)
    plan_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    plan_end: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_hours: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    drawing_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exception_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(lazy="joined")
    machine: Mapped[Machine | None] = relationship(lazy="joined")
    creator: Mapped[User | None] = relationship(foreign_keys="WorkOrder.created_by", lazy="joined")
