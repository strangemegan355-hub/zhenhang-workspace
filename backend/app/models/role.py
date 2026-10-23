from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import role_permission_association, user_role_association
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.user import User


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sys_roles"

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    data_scope: Mapped[str] = mapped_column(String(32), nullable=False, default="self", server_default="self")

    users: Mapped[list["User"]] = relationship(
        secondary=user_role_association,
        back_populates="roles",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permission_association,
        back_populates="roles",
    )
