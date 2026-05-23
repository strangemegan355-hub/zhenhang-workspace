from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class MachineCategory(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "machine_categories"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("machine_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[MachineCategory | None] = relationship(
        remote_side="MachineCategory.id",
        foreign_keys=[parent_id],
        back_populates="children",
    )
    children: Mapped[list[MachineCategory]] = relationship(back_populates="parent")
    machines: Mapped[list[Machine]] = relationship(back_populates="category")
    creator: Mapped["User | None"] = relationship(foreign_keys="MachineCategory.created_by", lazy="joined")


class Machine(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "machines"

    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("machine_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    machine_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    model_no: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[MachineCategory | None] = relationship(back_populates="machines")
    parameters: Mapped[list[MachineParameter]] = relationship(back_populates="machine")
    images: Mapped[list[MachineImage]] = relationship(back_populates="machine")
    boms: Mapped[list[MachineBom]] = relationship(back_populates="machine")
    creator: Mapped["User | None"] = relationship(foreign_keys="Machine.created_by", lazy="joined")


class MachineParameter(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "machine_parameters"

    machine_id: Mapped[UUID] = mapped_column(ForeignKey("machines.id", ondelete="CASCADE"), index=True)
    param_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    param_name: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    machine: Mapped[Machine] = relationship(back_populates="parameters")
    creator: Mapped["User | None"] = relationship(foreign_keys="MachineParameter.created_by", lazy="joined")


class MachineImage(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "machine_images"

    machine_id: Mapped[UUID] = mapped_column(ForeignKey("machines.id", ondelete="CASCADE"), index=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    machine: Mapped[Machine] = relationship(back_populates="images")
    creator: Mapped["User | None"] = relationship(foreign_keys="MachineImage.created_by", lazy="joined")


class MachineBom(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "machine_boms"

    machine_id: Mapped[UUID] = mapped_column(ForeignKey("machines.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    machine: Mapped[Machine] = relationship(back_populates="boms")
    items: Mapped[list[MachineBomItem]] = relationship(back_populates="bom")
    creator: Mapped["User | None"] = relationship(foreign_keys="MachineBom.created_by", lazy="joined")


class MachineBomItem(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "machine_bom_items"

    bom_id: Mapped[UUID] = mapped_column(ForeignKey("machine_boms.id", ondelete="CASCADE"), index=True)
    item_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    item_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    spec: Mapped[str | None] = mapped_column(String(160), nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    line_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    loss_rate: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    bom: Mapped[MachineBom] = relationship(back_populates="items")
    creator: Mapped["User | None"] = relationship(foreign_keys="MachineBomItem.created_by", lazy="joined")
