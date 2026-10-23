from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "audit_logs"

    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    creator: Mapped[User | None] = relationship(foreign_keys="AuditLog.created_by", lazy="joined")
