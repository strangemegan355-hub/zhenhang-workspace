from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.accounting_entry import AccountingEntry
    from app.models.procurement_entry import ProcurementEntry
    from app.models.user import User


class ProcurementPayableRequest(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "procurement_payable_requests"

    procurement_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("procurement_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[UUID] = mapped_column(
        ForeignKey("sys_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requested_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    approval_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending", index=True
    )
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payable_entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("accounting_entries.id", ondelete="SET NULL"),
        nullable=True,
    )

    procurement_entry: Mapped["ProcurementEntry"] = relationship(lazy="joined")
    requester: Mapped["User"] = relationship(foreign_keys=[requested_by], lazy="joined")
    approver: Mapped["User | None"] = relationship(foreign_keys=[approved_by], lazy="joined")
    payable_entry: Mapped["AccountingEntry | None"] = relationship(lazy="joined")
