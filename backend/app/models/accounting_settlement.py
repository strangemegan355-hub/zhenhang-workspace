from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.accounting_entry import AccountingEntry


class AccountingSettlement(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "accounting_settlements"

    receipt_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounting_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    receivable_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounting_entries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    receipt_entry: Mapped[AccountingEntry] = relationship(foreign_keys=[receipt_entry_id], lazy="joined")
    receivable_entry: Mapped[AccountingEntry] = relationship(foreign_keys=[receivable_entry_id], lazy="joined")
