from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.equipment_unit import EquipmentUnit
    from app.models.machine import Machine
    from app.models.user import User


class AcceptanceTemplate(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "acceptance_templates"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template_type: Mapped[str] = mapped_column(
        String(8), nullable=False, index=True, comment="fat|sat"
    )
    machine_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("machines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    items: Mapped[list | None] = mapped_column(JSONB, nullable=True, comment="[{category, check_point, standard, method}]")

    machine: Mapped[Machine | None] = relationship()
    records: Mapped[list[AcceptanceRecord]] = relationship(back_populates="template")
    creator: Mapped[User | None] = relationship(foreign_keys="AcceptanceTemplate.created_by", lazy="joined")


class AcceptanceRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "acceptance_records"

    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("acceptance_templates.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    equipment_unit_id: Mapped[UUID] = mapped_column(
        ForeignKey("equipment_units.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    record_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    test_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    inspector_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="in_progress", server_default="in_progress",
        comment="in_progress|passed|failed"
    )
    items: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, comment="[{category, check_point, standard, actual_result, pass, remark}]"
    )
    overall_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped[AcceptanceTemplate] = relationship(back_populates="records")
    equipment_unit: Mapped[EquipmentUnit] = relationship()
    punch_items: Mapped[list[PunchListItem]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )
    creator: Mapped[User | None] = relationship(foreign_keys="AcceptanceRecord.created_by", lazy="joined")


class PunchListItem(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "punch_list_items"

    record_id: Mapped[UUID] = mapped_column(
        ForeignKey("acceptance_records.id", ondelete="CASCADE"), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(12), nullable=False, default="minor", server_default="minor",
        comment="critical|major|minor"
    )
    status: Mapped[str] = mapped_column(
        String(12), nullable=False, default="open", server_default="open",
        comment="open|resolved"
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    record: Mapped[AcceptanceRecord] = relationship(back_populates="punch_items")
    creator: Mapped[User | None] = relationship(foreign_keys="PunchListItem.created_by", lazy="joined")
