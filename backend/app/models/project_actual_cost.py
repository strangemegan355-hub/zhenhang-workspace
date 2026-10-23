from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.supplier import Supplier
    from app.models.user import User


class ProjectActualCost(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "project_actual_costs"

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cost_category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    cost_item_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cost_item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="采购", server_default="采购")
    supplier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    procurement_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    project: Mapped[Project] = relationship(lazy="joined")
    supplier: Mapped[Supplier | None] = relationship(lazy="joined")
    creator: Mapped[User | None] = relationship(foreign_keys="ProjectActualCost.created_by", lazy="joined")
