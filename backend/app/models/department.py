from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sys_departments"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sys_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[Department | None] = relationship(
        remote_side="Department.id",
        foreign_keys=[parent_id],
        back_populates="children",
    )
    children: Mapped[list[Department]] = relationship(
        back_populates="parent",
        cascade="save-update, merge",
    )
    users: Mapped[list[User]] = relationship(back_populates="department")
