from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "customers"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    level: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    contacts: Mapped[list[CustomerContact]] = relationship(back_populates="customer")
    followups: Mapped[list[CustomerFollowup]] = relationship(back_populates="customer")
    creator: Mapped["User | None"] = relationship(foreign_keys="Customer.created_by", lazy="joined")


class CustomerContact(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "customer_contacts"

    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    position: Mapped[str | None] = mapped_column(String(80), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wechat: Mapped[str | None] = mapped_column(String(80), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="contacts")
    followups: Mapped[list[CustomerFollowup]] = relationship(back_populates="contact")
    creator: Mapped["User | None"] = relationship(foreign_keys="CustomerContact.created_by", lazy="joined")


class CustomerFollowup(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "customer_followups"

    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customer_contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    followup_type: Mapped[str] = mapped_column(String(32), nullable=False, default="phone", server_default="phone")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    followup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="followups")
    contact: Mapped[CustomerContact | None] = relationship(back_populates="followups")
    creator: Mapped["User | None"] = relationship(foreign_keys="CustomerFollowup.created_by", lazy="joined")
