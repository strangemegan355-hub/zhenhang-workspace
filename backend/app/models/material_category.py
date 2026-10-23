from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class MaterialCategory(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "material_categories"

    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("material_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scope: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[MaterialCategory | None] = relationship(
        remote_side="MaterialCategory.id",
        foreign_keys=[parent_id],
        back_populates="children",
    )
    children: Mapped[list[MaterialCategory]] = relationship(back_populates="parent")
    creator: Mapped[User | None] = relationship(foreign_keys="MaterialCategory.created_by", lazy="joined")
