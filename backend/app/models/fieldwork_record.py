from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.aftersales_service_request import AfterSalesServiceRequest
    from app.models.customer import Customer
    from app.models.machine import Machine
    from app.models.material import Material
    from app.models.project import Project
    from app.models.user import User


class FieldworkRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "fieldwork_records"

    record_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    record_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="submitted", server_default="submitted", index=True)
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    machine_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("machines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    material_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("materials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    occurred_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    reporter_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    qty: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    hours: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    repair_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    receivable_entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("accounting_entries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    service_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("aftersales_service_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer | None"] = relationship(lazy="joined")
    project: Mapped["Project | None"] = relationship(lazy="joined")
    machine: Mapped["Machine | None"] = relationship(lazy="joined")
    material: Mapped["Material | None"] = relationship(lazy="joined")
    creator: Mapped["User | None"] = relationship(foreign_keys="FieldworkRecord.created_by", lazy="joined")
    service_request: Mapped["AfterSalesServiceRequest | None"] = relationship(lazy="joined")
