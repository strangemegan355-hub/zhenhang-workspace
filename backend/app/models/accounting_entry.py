from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.accounting_entry_line import AccountingEntryLine
    from app.models.customer import Customer
    from app.models.project import Project
    from app.models.quote import Quote
    from app.models.supplier import Supplier
    from app.models.user import User


class AccountingEntry(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "accounting_entries"

    entry_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    entry_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft", index=True)
    party_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quote_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    settled_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY", server_default="CNY")
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    booked_on: Mapped[date] = mapped_column(Date, nullable=False)
    is_backfill: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual", server_default="manual")
    source_id: Mapped[UUID | None] = mapped_column(nullable=True)
    source_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="none", server_default="none")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer | None"] = relationship(lazy="joined")
    supplier: Mapped["Supplier | None"] = relationship(lazy="joined")
    project: Mapped["Project | None"] = relationship(lazy="joined")
    quote: Mapped["Quote | None"] = relationship(lazy="joined")
    creator: Mapped["User | None"] = relationship(foreign_keys="AccountingEntry.created_by", lazy="joined")
    lines: Mapped[list["AccountingEntryLine"]] = relationship(
        back_populates="entry",
        lazy="selectin",
        order_by="AccountingEntryLine.sort_order",
    )
