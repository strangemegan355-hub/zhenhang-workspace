from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import role_permission_association
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.role import Role


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sys_permissions"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    resource: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list[Role]] = relationship(
        secondary=role_permission_association,
        back_populates="permissions",
    )
