from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class WorkflowState(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "workflow_states"

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_start: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    creator: Mapped["User | None"] = relationship(foreign_keys="WorkflowState.created_by", lazy="joined")


class WorkflowTransition(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "workflow_transitions"

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    from_state_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_states.id", ondelete="CASCADE"), index=True)
    to_state_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_states.id", ondelete="CASCADE"), index=True)
    action_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    from_state: Mapped[WorkflowState] = relationship(foreign_keys=[from_state_id])
    to_state: Mapped[WorkflowState] = relationship(foreign_keys=[to_state_id])
    creator: Mapped["User | None"] = relationship(foreign_keys="WorkflowTransition.created_by", lazy="joined")
