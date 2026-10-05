from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.equipment_unit import EquipmentUnit
    from app.models.user import User


class InstallationPlan(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    """Installation + commissioning + customer acceptance for an equipment unit."""

    __tablename__ = "installation_plans"

    equipment_unit_id: Mapped[UUID] = mapped_column(
        ForeignKey("equipment_units.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    planned_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="planned", server_default="planned",
        comment="planned|in_progress|completed"
    )
    install_items: Mapped[list | None] = mapped_column(
        JSONB, nullable=True,
        comment="[{step, description, completed, completed_at, remark}]"
    )
    commissioning_items: Mapped[list | None] = mapped_column(
        JSONB, nullable=True,
        comment="[{category, check_point, expected, actual_result, pass, remark}]"
    )
    customer_representative: Mapped[str | None] = mapped_column(String(120), nullable=True)
    customer_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    customer_accepted_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    equipment_unit: Mapped[EquipmentUnit] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys="InstallationPlan.created_by", lazy="joined")
