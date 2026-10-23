from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.project import Project
    from app.models.supplier import Supplier
    from app.models.user import User


class ProcurementEntry(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "procurement_entries"

    request_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    material_id: Mapped[UUID] = mapped_column(
        ForeignKey("materials.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    qty: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    lead_days: Mapped[int] = mapped_column(nullable=False, default=7, server_default="7")
    need_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", server_default="planned", index=True)
    transferred_to_actual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    payable_status: Mapped[str] = mapped_column(String(32), nullable=False, default="none", server_default="none", index=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project | None] = relationship(lazy="joined")
    material: Mapped[Material] = relationship(lazy="joined")
    supplier: Mapped[Supplier] = relationship(lazy="joined")
    creator: Mapped[User | None] = relationship(foreign_keys="ProcurementEntry.created_by", lazy="joined")
