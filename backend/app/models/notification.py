from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class NotificationProvider(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "notification_providers"

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # email/sms/webhook/inapp
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    creator: Mapped["User | None"] = relationship(foreign_keys="NotificationProvider.created_by", lazy="joined")


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "notifications"

    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="inapp", server_default="inapp", index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    biz_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    biz_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    receiver_id: Mapped[UUID | None] = mapped_column(ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("notification_providers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    receiver: Mapped["User | None"] = relationship(foreign_keys=[receiver_id])
    provider: Mapped[NotificationProvider | None] = relationship()
    creator: Mapped["User | None"] = relationship(foreign_keys="Notification.created_by", lazy="joined")
