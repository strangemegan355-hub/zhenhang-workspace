from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.accounting_entry import AccountingEntry
    from app.models.product import Product


class AccountingEntryLine(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "accounting_entry_lines"

    entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounting_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_name: Mapped[str] = mapped_column(String(160), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(200), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1, server_default="1")
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    line_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    entry: Mapped["AccountingEntry"] = relationship(back_populates="lines")
    product: Mapped["Product | None"] = relationship(lazy="joined")
