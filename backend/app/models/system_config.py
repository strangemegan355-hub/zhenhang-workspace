from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class SystemConfig(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "system_configs"

    key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False, default="string", server_default="string")
    group: Mapped[str] = mapped_column(String(64), nullable=False, default="default", server_default="default", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    creator: Mapped[User | None] = relationship(foreign_keys="SystemConfig.created_by", lazy="joined")
