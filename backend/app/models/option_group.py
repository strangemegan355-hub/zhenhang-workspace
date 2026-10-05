from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.machine import Machine
    from app.models.user import User


class OptionGroup(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "option_groups"

    machine_id: Mapped[UUID] = mapped_column(
        ForeignKey("machines.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    machine: Mapped[Machine] = relationship(back_populates="option_groups")
    items: Mapped[list[OptionItem]] = relationship(
        back_populates="option_group", cascade="all, delete-orphan", order_by="OptionItem.sort_order"
    )
    creator: Mapped[User | None] = relationship(foreign_keys="OptionGroup.created_by", lazy="joined")


class OptionItem(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "option_items"

    option_group_id: Mapped[UUID] = mapped_column(
        ForeignKey("option_groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_adjustment: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, server_default="0"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    option_group: Mapped[OptionGroup] = relationship(back_populates="items")
    creator: Mapped[User | None] = relationship(foreign_keys="OptionItem.created_by", lazy="joined")
