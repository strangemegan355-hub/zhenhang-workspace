from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.machine import Machine
    from app.models.project import Project
    from app.models.user import User


class EquipmentUnit(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    """Serial-numbered equipment unit — a concrete instance of a Machine model."""

    __tablename__ = "equipment_units"

    serial_number: Mapped[str] = mapped_column(
        String(80), unique=True, index=True, nullable=False
    )
    machine_id: Mapped[UUID] = mapped_column(
        ForeignKey("machines.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    build_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="in_production", server_default="in_production",
        comment="in_production|in_stock|shipped|installed|running|under_maintenance|decommissioned"
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True, nullable=True
    )
    build_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    install_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    acceptance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    warranty_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    machine: Mapped[Machine] = relationship(foreign_keys=[machine_id])
    project: Mapped[Project | None] = relationship(foreign_keys=[project_id])
    customer: Mapped[Customer | None] = relationship(foreign_keys=[customer_id])
    creator: Mapped[User | None] = relationship(foreign_keys="EquipmentUnit.created_by", lazy="joined")
