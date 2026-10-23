from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.equipment_unit import EquipmentUnit
    from app.models.user import User


class AfterSalesServiceRequest(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "aftersales_service_requests"

    request_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    equipment_unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("equipment_units.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft", index=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", server_default="medium")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True)
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(lazy="joined")
    equipment_unit: Mapped[EquipmentUnit | None] = relationship(lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assigned_to], lazy="joined")
    creator: Mapped[User | None] = relationship(foreign_keys="AfterSalesServiceRequest.created_by", lazy="joined")
